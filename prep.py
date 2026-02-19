import os
import shutil
from fastapi import APIRouter, Depends, File, UploadFile
from pathlib import Path
import zipfile
from app.schemas.prep import PowerQueryRequest
from app.core import STORAGE_BASE_DIR, PREP_FILE_OUTPUT_DIR, FLOW_FILE_NAME
from app.core.dependencies import get_current_user
from app.core import logger
from fastapi import HTTPException, status
# from app.services.prep.power_query import generate_power_queries
from app.services.prep.get_hyper_file import build_tableau_lookup, parse_level_names
from app.services.prep.prep_service import save_execution_tree, convert_tfl_to_tflx
from app.core.config import S3Config, BlobConfig, TableauConfig
from app.core.constants import LOCAL_PREP_INPUT_SUBDIR, LOCAL_PREP_OUTPUT_SUBDIR, S3_PREP_INPUT_FILE_PATH, S3_PREP_INPUT_FOLDER, S3_PREP_OUTPUT_FOLDER, POWER_BI_PATH, LOCAL_POWER_BI_PATH
# from app.services.prep.power_query import build_output_s3_key, build_s3_key, generate_power_queries, generate_power_queries_async, generate_power_query_blocks
import json
from app.services.prep.level_wise_power_Query import generate_power_query_blocks
from app.services.prep.prep_helper import build_s3_key, build_output_s3_key
from app.services.prep.update_tables import update_tmdl_files


tableau_config = TableauConfig()
prep_router = APIRouter()

# Initialize cloud storage based on CLOUD_PROVIDER environment variable
cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower().strip()
if cloud_provider == "azure":
    cloud_storage = BlobConfig()
    logger.info(f"[PREP_API] Initialized AZURE BLOB storage client")
else:
    cloud_storage = S3Config()
    logger.info(f"[PREP_API] Initialized AWS S3 storage client")

@prep_router.post("/prep_files/extract_flow_structure")
async def extract_flow_structure(
    uploaded_file: UploadFile = File(...),
    ):
    """
    Unzips a Tableau Prep `.tflx` file, extracts the `flow` JSON,
    parses it into a tree structure, and saves the result locally.

    Parameters
    ----------
    request : PrepRequest
        Request containing the input `.tflx` or `.tfl` file path and
        the desired extraction path.

    Returns
    -------
    dict
        A message confirming success or an error.
    """

    output_dir = STORAGE_BASE_DIR/PREP_FILE_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    original_filename = uploaded_file.filename
    file_suffix = Path(original_filename).suffix.lower()

    local_path = output_dir / original_filename
    with open(local_path, "wb") as f:
        content = await uploaded_file.read()
        f.write(content)

    if file_suffix == ".tfl":
        tflx_path = local_path.with_suffix(".tflx")
        convert_tfl_to_tflx(local_path, tflx_path)
        local_path = tflx_path
        original_filename = tflx_path.name

    s3_key_uploaded = f"{S3_PREP_INPUT_FILE_PATH}/{original_filename}"
    
    # Upload TFLX file to cloud storage
    if cloud_provider == "azure":
        await cloud_storage.upload_to_blob(str(local_path), s3_key_uploaded)
    else:
        await cloud_storage.upload_to_s3(str(local_path), s3_key_uploaded)

    extract_path = output_dir / "extracted_files"
    extract_path.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(local_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    except zipfile.BadZipFile:
        logger.exception("The provided file is not a valid ZIP archive.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ZIP file.")


    flow_file = next((f for f in extract_path.rglob(FLOW_FILE_NAME) if f.is_file()), None)
    if not flow_file or not flow_file.exists() or flow_file.stat().st_size == 0:
        logger.error("Invalid or empty 'flow' file.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or empty 'flow' file.")
    
    filename_stem = Path(original_filename).stem
    structured_filename = f"{filename_stem}_structured.json"
    analysis_filename = f"{filename_stem}_analysis.docx"

    output_json_path = output_dir / f"{filename_stem}.json"
    save_execution_tree(flow_file, output_json_path)

    s3_structured_key = f"Prep_files/Structured_json/{structured_filename}"
    
    # Upload structured JSON to cloud storage
    if cloud_provider == "azure":
        await cloud_storage.upload_to_blob(str(output_json_path), s3_structured_key)
    else:
        await cloud_storage.upload_to_s3(str(output_json_path), s3_structured_key)

    docx_file_path = output_json_path.with_suffix(".docx")
    s3_docx_key = f"Prep_files/Analysis_docx/{analysis_filename}"
    
    # Upload analysis DOCX to cloud storage
    if cloud_provider == "azure":
        await cloud_storage.upload_to_blob(str(docx_file_path), s3_docx_key)
    else:
        await cloud_storage.upload_to_s3(str(docx_file_path), s3_docx_key)

    # Generate presigned URLs
    structured_presigned_url = await cloud_storage.generate_presigned_url(s3_structured_key)
    analysis_presigned_url = await cloud_storage.generate_presigned_url(s3_docx_key)
    shutil.rmtree(output_dir, ignore_errors=True)

    return {
        "message": "Flow extracted and uploaded successfully.",
        "flow_json": {
            "url": structured_presigned_url,
            "name": structured_filename
        },
        "flow_docx": {
            "url": analysis_presigned_url,
            "name": analysis_filename
        }
    }


@prep_router.post("/prep_files/generate_power_query")
async def generate_power_query_enhanced(request: PowerQueryRequest):
    """
    Enhanced Power Query generation using level-wise approach

    This endpoint uses the new level-wise generation approach that:
    - Processes execution levels sequentially
    - Handles complex transformations and joins properly
    - Provides better syntax validation and error handling
    - Supports dynamic node references and fallback generation
    """

    try:
        input_filename = Path(request.prep_flow_file).name
        base_name = input_filename.split("_structured")[0]

        input_local_dir = STORAGE_BASE_DIR / PREP_FILE_OUTPUT_DIR / LOCAL_PREP_INPUT_SUBDIR
        input_local_path = input_local_dir / input_filename

        output_local_dir = STORAGE_BASE_DIR/PREP_FILE_OUTPUT_DIR / LOCAL_PREP_OUTPUT_SUBDIR
        output_local_path = output_local_dir / input_filename

        power_bi_dir = STORAGE_BASE_DIR/LOCAL_POWER_BI_PATH
        zip_target_path = power_bi_dir.with_suffix(".zip")

        output_powerbi_zip = f"{base_name}.zip"
        output_s3_key = f"{S3_PREP_OUTPUT_FOLDER}/{output_powerbi_zip}"

        input_local_dir.mkdir(parents=True, exist_ok=True)
        output_local_dir.mkdir(parents=True, exist_ok=True)

        # Download prep flow file from cloud storage
        s3_input_key = build_s3_key(S3_PREP_INPUT_FOLDER, request.prep_flow_file)
        await cloud_storage.download_file(s3_input_key, str(input_local_path))
        
        # Download PowerBI template from cloud storage
        await cloud_storage.download_file(POWER_BI_PATH, str(zip_target_path))

        with zipfile.ZipFile(zip_target_path, 'r') as zip_ref:
            zip_ref.extractall(power_bi_dir)

        # try:
        #     original_folder = next(item for item in power_bi_dir.iterdir() if item.is_dir())
        # except StopIteration:
        #     raise RuntimeError("No folders found in Power BI zip extraction.")

        # renamed_folder = power_bi_dir / base_name
        # original_folder.rename(renamed_folder)
        # power_bi_dir = renamed_folder

        # # Rename all items (files and folders) inside the renamed folder
        # for item in power_bi_dir.iterdir():
        #     parts = item.name.split("_", 1)
        #     new_name = f"{base_name}_{parts[1]}" if len(parts) == 2 else f"{base_name}_{item.name}"
        #     new_path = item.parent / new_name
        #     item.rename(new_path)

        with open(input_local_path, "r", encoding="utf-8") as f:
            prep_json = json.load(f)

        power_query_blocks = await generate_power_query_blocks(prep_json)

        # Format the blocks into a single string
        formatted_output = ""
        for level_name, code in power_query_blocks:
            formatted_output += f"// ===== {level_name} =====\n"
            formatted_output += code + "\n\n"

        with open(output_local_path, "w", encoding="utf-8") as f:
            f.write(formatted_output)
        
        level_to_ds = parse_level_names(power_query_blocks)
        tableau_columns_lookup = build_tableau_lookup(level_to_ds, tableau_config)
        update_tmdl_files(power_bi_dir, output_local_path, tableau_columns_lookup)

        with zipfile.ZipFile(output_powerbi_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(power_bi_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    arc_name = os.path.relpath(abs_path, power_bi_dir.parent)
                    zipf.write(abs_path, arc_name)

        # Upload modified Power BI zip to cloud storage
        if cloud_provider == "azure":
            await cloud_storage.upload_to_blob(output_powerbi_zip, output_s3_key)
        else:
            await cloud_storage.upload_to_s3(output_powerbi_zip, output_s3_key)
        
        presigned_url = await cloud_storage.generate_presigned_url(output_s3_key)

        shutil.rmtree(STORAGE_BASE_DIR, ignore_errors=True)

        return {
            "message": f"Updated Power BI zip uploaded to {cloud_provider.upper()} storage",
            "file_name": base_name,
            "presigned_url": presigned_url
        }

    except Exception as e:
        logger.error(f"Error in Power Query processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


    
