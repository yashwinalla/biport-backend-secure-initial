import os
import logging
import aiofiles
import aioboto3
import botocore
from typing import Optional, List
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from openai import OpenAI
from dotenv import load_dotenv
from app.core.constants import HTTP_STATUS_INTERNAL_ERROR, MSG_S3_DOWNLOAD_FAILED, MSG_S3_FETCH_ERROR
from fastapi import HTTPException, status
from pathlib import Path
import tableauserverclient as TSC
from app.core.exceptions import BadRequestError
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from datetime import datetime, timedelta, timezone
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from urllib.parse import quote
from openai import AzureOpenAI



# Load environment variables
load_dotenv()

def setup_logger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers if the logger was already configured
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler for logging to stdout
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
    )
    logger.addHandler(console_handler)

    return logger

logger = setup_logger("BIport-Log")

#for semantic_model V2 api
class PathConfig:
    powerbi_structure_path = 'demo_files/powerbi_structure'
    semantic_model_path = 'static/semantic_model_structure'
    dateTable_template_path = 'static/DateTemplate.tmdl'

# Local storage path configuration with shortened paths
class LocalPathConfig:
    """Configuration for local ./storage paths with shortened names and UUID prefixes"""
    
    @staticmethod
    def get_short_uuid(uuid_str: str) -> str:
        """Get first 6 characters of UUID string"""
        return str(uuid_str)[:6]
    
    @staticmethod
    def get_analysis_path(uuid_str: str) -> str:
        """Get local analysis output path: ./storage/{6_char_uuid}/ansys/"""
        short_uuid = LocalPathConfig.get_short_uuid(uuid_str)
        return f"./storage/{short_uuid}/ansys"
    
    @staticmethod
    def get_conversion_path(uuid_str: str) -> str:
        """Get local DAX conversion output path: ./storage/{6_char_uuid}/dax/"""
        short_uuid = LocalPathConfig.get_short_uuid(uuid_str)
        return f"./storage/{short_uuid}/dax"
    
    @staticmethod
    def get_migration_path(uuid_str: str) -> str:
        """Get local migration output path: ./storage/{6_char_uuid}/mig/"""
        short_uuid = LocalPathConfig.get_short_uuid(uuid_str)
        return f"./storage/mig/{short_uuid}"
    
    @staticmethod
    def get_base_storage_path(uuid_str: str) -> str:
        """Get base storage path: ./storage/{6_char_uuid}/"""
        short_uuid = LocalPathConfig.get_short_uuid(uuid_str)
        return f"./storage/{short_uuid}"

class S3Config(BaseSettings):
    region_name: str = os.getenv("AWS_REGION")
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_KEY")
    endpoint_url: str = os.getenv("AWS_ENDPOINT")
    bucket_name: str = os.getenv("AWS_S3_BUCKET_NAME")
 
    def get_s3_client(self):
        return aioboto3.Session().client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            endpoint_url=self.endpoint_url,
        )
                
    async def upload_to_s3(self, file_path: str, object_name: str) -> bool:
        try:
            async with self.get_s3_client() as s3:
                with open(file_path, "rb") as f:
                    await s3.upload_fileobj(f, self.bucket_name, object_name)
            return True
        except Exception as e:
            logger.error(f"Upload to S3 failed: {e}")
            return False

    async def check_file_exists(self, object_name: str) -> bool:
        """
        Checks whether an object exists in the S3 bucket.
        Returns True if it exists, False if not found, raises exception for other errors.
        """
        try:
            async with self.get_s3_client() as s3:
                await s3.head_object(Bucket=self.bucket_name, Key=object_name)
                return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            # Re-raise other client errors (permissions, etc)
            raise
        except Exception as e:
            logger.error(f"Error checking S3 file existence: {str(e)}")
            raise

    async def copy_object(self, source_key: str, destination_key: str) -> bool:
        """
        Copies an object from source_key to destination_key within the same bucket.
        Returns True if successful, otherwise False.
        """
        try:
            async with self.get_s3_client() as s3:
                copy_source = {"Bucket": self.bucket_name, "Key": source_key}
                await s3.copy_object(Bucket=self.bucket_name, CopySource=copy_source, Key=destination_key)
            return True
        except Exception as e:
            logger.error(f"Copy object in S3 failed: {e}")
            return False

    async def delete_object(self, object_key: str) -> bool:
        """
        Deletes an object from the S3 bucket.
        Returns True if successful, otherwise False.
        """
        try:
            async with self.get_s3_client() as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except Exception as e:
            logger.error(f"Delete object from S3 failed: {e}")
            return False

    async def download_file(self, object_name: str, file_path: str) -> None:
        """Downloads an object from S3 to a local file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            async with self.get_s3_client() as s3:
                async with aiofiles.open(file_path, "wb") as f:
                    await s3.download_fileobj(self.bucket_name, object_name, f)
        except Exception as e:
            raise BadRequestError(
                status_code=404,
                detail=f"Failed to download file from s3: {str(e)}"
            )

    async def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        try:
            async with self.get_s3_client() as s3_client:
                return await s3_client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": self.bucket_name, "Key": object_key},
                    ExpiresIn=expiration,
                )
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
        
    @staticmethod
    def extract_s3_key(filepath: str, bucket_name: str) -> str:
        return filepath.replace(f"s3://{bucket_name}/", "")
    
    async def get_twb_files(self,
                            s3_input_path,
                            local_download_path):
            try:
                async with self.get_s3_client() as s3_client:
                        response = await s3_client.list_objects_v2(
                            Bucket = self.bucket_name, 
                            Prefix = s3_input_path.lstrip("/")
                        )
                        if "Contents" not in response:
                            raise HTTPException(
                                status_code = 400,
                                detail = "No files found in S3 input path",
                            )
                        twb_files_path = []
                        for obj in response["Contents"]:
                            file_key = obj["Key"]
                            file_name = os.path.basename(file_key)
                            local_file_path = os.path.join(local_download_path, file_name)
                            await s3_client.download_file(
                                                        self.bucket_name,
                                                        file_key,
                                                        local_file_path,
                                                        )
                            twb_files_path.append(local_file_path)
                        return twb_files_path
            except Exception as s3er:
                raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail = f"Problem in fetching previous data: {str(s3er)}")

    async def download_twb_file_from_s3(self,
                            s3_key: str,
                            local_download_path: str) -> list[str]:
            """
            Download a .twb file from S3 to a local path.

            Parameters
            ----------
            s3_key : str
                The S3 object key of the .twb file to download.
            local_download_path : str
                The local directory where the file should be saved.

            Returns
            -------
            List containing the local file path of the downloaded file.
            """

            try:
                local_dir = Path(local_download_path)
                local_dir.mkdir(parents=True, exist_ok=True)
                # os.makedirs(local_download_path, exist_ok=True)
        
                # Extract the file name from the input path
                file_name = Path(s3_key).name
                local_file_path = local_dir / file_name

                async with self.get_s3_client() as s3_client:
                    try:
                        # Download the file from S3 to the local path
                        async with aiofiles.open(local_file_path, 'wb') as local_file:
                            await s3_client.download_fileobj(
                                Bucket=self.bucket_name,
                                Key=s3_key,
                                Fileobj=local_file
                            )
                        return [str(local_file_path)]
                    except Exception as error:
                        logger.exception(f"S3 download error: {error}")
                        raise HTTPException(
                            status_code=HTTP_STATUS_INTERNAL_ERROR,
                            detail=MSG_S3_DOWNLOAD_FAILED
                        )
            except Exception as s3_error:
                logger.exception(f"Local setup error: {s3_error}")
                raise HTTPException(status_code = HTTP_STATUS_INTERNAL_ERROR,
                                    detail = MSG_S3_FETCH_ERROR)
            


    async def download_semantic_model_input_files(
        self,
        s3_input_prefix: str,
        local_download_path: str,
        allowed_extensions: List[str] = [".twb", ".csv", ".xlsx"]
    ) -> List[str]:
        """
        Downloads all semantic model input files (filtered by extension) from a given S3 prefix to local path.

        Args:
            s3_input_prefix (str): The S3 folder/prefix (e.g., org/email/process_id/input_files)
            local_download_path (str): Local path to store the files.
            allowed_extensions (List[str], optional): File types to download. Defaults to common types.

        Returns:
            List[str]: List of downloaded local file paths.
        """
        try:
            os.makedirs(local_download_path, exist_ok=True)
            downloaded_files = []

            async with self.get_s3_client() as s3_client:
                response = await s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=s3_input_prefix.rstrip("/") + "/"
                )

                if "Contents" not in response or not response["Contents"]:
                    logger.warning(f"No files found at S3 prefix: {s3_input_prefix}")
                    return []

                for obj in response["Contents"]:
                    file_key = obj["Key"]
                    file_name = os.path.basename(file_key)

                    # Skip if not a file or if the extension isn't allowed
                    if not file_name or (allowed_extensions and Path(file_name).suffix.lower() not in allowed_extensions):
                        continue

                    local_file_path = os.path.join(local_download_path, file_name)

                    try:
                        # Stream download to local
                        async with aiofiles.open(local_file_path, "wb") as f:
                            response_stream = await s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
                            async for chunk in response_stream["Body"]:
                                await f.write(chunk)
                        downloaded_files.append(local_file_path)
                        logger.info(f"Downloaded {file_key} to {local_file_path}")

                    except Exception as e:
                        logger.error(f"Failed to download {file_key}: {e}")

            return downloaded_files

        except Exception as err:
            logger.exception(f"Failed to download semantic input files from {s3_input_prefix}: {err}")
            raise HTTPException(status_code=500, detail="Failed to download semantic model input files from S3")
    
    async def copy_all_folder_files_to_local_path(
        self,
        s3_folder_prefix: str,
        local_path_for_copy: str
    ) -> List[str]:
        """
        Downloads ALL files (recursively) from a given S3 folder/prefix to the specified local directory.
        Flattens the structure (just uses filenames), so duplicate names will overwrite.
        """
        downloaded_files = []
        try:
            os.makedirs(local_path_for_copy, exist_ok=True)
            async with self.get_s3_client() as s3_client:
                # List all objects under the prefix
                paginator = s3_client.get_paginator('list_objects_v2')
                async for result in paginator.paginate(Bucket=self.bucket_name, Prefix=s3_folder_prefix.rstrip("/") + "/"):
                    contents = result.get("Contents", [])
                    if not contents:
                        logger.warning(f"No files found in S3 folder: {s3_folder_prefix}")
                        return []
                    for obj in contents:
                        file_key = obj["Key"]
                        file_name = os.path.basename(file_key)
                        local_file_path = os.path.join(local_path_for_copy, file_name)
                        try:
                            async with aiofiles.open(local_file_path, "wb") as local_file:
                                obj_body = await s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
                                async for chunk in obj_body["Body"]:
                                    await local_file.write(chunk)
                            downloaded_files.append(local_file_path)
                            logger.info(f"Copied {file_key} to {local_file_path}")
                        except Exception as e:
                            logger.error(f"Failed to download {file_key} from S3: {e}")
            return downloaded_files
        except Exception as e:
            logger.error(f"Error copying files from S3 folder {s3_folder_prefix}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in downloading files to local path: {str(e)}"
            )




class BlobConfig(BaseSettings):
    connection_string: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name: str = os.getenv("AZURE_BLOB_CONTAINER_NAME")
 
    def get_blob_client(self):
        return BlobServiceClient.from_connection_string(self.connection_string)
                
    async def upload_to_blob(self, file_path: str, object_name: str) -> bool:
        try:
            try:
                blob_service_client = self.get_blob_client()
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=object_name
                )
                with open(file_path, "rb") as f:
                    await blob_client.upload_blob(f, overwrite=True)
                return True
            finally:
                await blob_service_client.close()
        except Exception as e:
            logger.error(f"Upload to Blob failed: {e}")
            return False

    async def check_file_exists(self, object_name: str) -> bool:
        """
        Checks whether an object exists in the Blob container.
        Returns True if it exists, False if not found, raises exception for other errors.
        """
        try:
            try:
                blob_service_client = self.get_blob_client()
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=object_name
                )
                await blob_client.get_blob_properties()
                return True
            finally:
                await blob_service_client.close()
        except ResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking Blob file existence: {str(e)}")
            raise

    async def copy_object(self, source_key: str, destination_key: str) -> bool:
        """
        Copies an object from source_key to destination_key within the same container.
        Returns True if successful, otherwise False.
        """
        try:
            try:
                blob_service_client = self.get_blob_client()
                source_blob_client = blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=source_key
                )
                destination_blob_client = blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=destination_key
                )
                
                # Get the source blob URL
                source_url = source_blob_client.url
                await destination_blob_client.start_copy_from_url(source_url)
                return True
            finally:
                await blob_service_client.close()
        except Exception as e:
            logger.error(f"Copy object in Blob failed: {e}")
            return False

    async def delete_object(self, object_key: str) -> bool:
        """
        Deletes an object from the Blob container.
        Returns True if successful, otherwise False.
        """
        try:
            try:
                blob_service_client = self.get_blob_client()
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=object_key
                )
                await blob_client.delete_blob()
                return True
            finally:
                await blob_service_client.close()
        except Exception as e:
            logger.error(f"Delete object from Blob failed: {e}")
            return False

    async def download_file(self, object_name: str, file_path: str) -> None:
        """Downloads an object from Blob to a local file."""
        try:
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                blob_service_client = self.get_blob_client()
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=object_name
                )
                async with aiofiles.open(file_path, "wb") as f:
                    download_stream = await blob_client.download_blob()
                    async for chunk in download_stream.chunks():
                        await f.write(chunk)
            finally:
                await blob_service_client.close()
        except Exception as e:
            raise BadRequestError(
                status_code=404,
                detail=f"Failed to download file from blob: {str(e)}"
            )

    async def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        try:
            conn_str_dict = dict(item.split('=', 1) for item in self.connection_string.split(';') if '=' in item)
            account_name = conn_str_dict.get('AccountName')
            account_key = conn_str_dict.get('AccountKey')
            
            if not account_name or not account_key:
                logger.error("Could not extract account credentials from connection string for SAS generation")
                return None
            
            # Generate SAS token with proper UTC time
            start_time = datetime.now(timezone.utc)
            expiry_time = start_time + timedelta(seconds=expiration)
            
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.container_name,
                blob_name=object_key,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                start=start_time,
                expiry=expiry_time
            )
            
            encoded_blob_name = quote(object_key, safe='/')
            blob_url = f"https://{account_name}.blob.core.windows.net/{self.container_name}/{encoded_blob_name}?{sas_token}"
            return blob_url
            
        except Exception as e:
            logger.error(f"Error generating presigned URL for Azure Blob: {e}")
            return None
        
    @staticmethod
    def extract_blob_key(filepath: str, container_name: str) -> str:
        return filepath.replace(f"blob://{container_name}/", "")
    
    async def get_twb_files(self,
                            blob_input_path,
                            local_download_path):
            try:
                try:
                    blob_service_client = self.get_blob_client()
                    container_client = blob_service_client.get_container_client(self.container_name)
                    
                    blob_list = container_client.list_blobs(name_starts_with=blob_input_path.lstrip("/"))
                    blob_files = list(blob_list)
                    
                    if not blob_files:
                        raise HTTPException(
                            status_code = 400,
                            detail = "No files found in Blob input path",
                        )
                    
                    twb_files_path = []
                    for blob in blob_files:
                        file_key = blob.name
                        file_name = os.path.basename(file_key)
                        local_file_path = os.path.join(local_download_path, file_name)
                        
                        blob_client = blob_service_client.get_blob_client(
                            container=self.container_name, 
                            blob=file_key
                        )
                        async with aiofiles.open(local_file_path, "wb") as f:
                            download_stream = await blob_client.download_blob()
                            async for chunk in download_stream.chunks():
                                await f.write(chunk)
                        twb_files_path.append(local_file_path)
                    return twb_files_path
                finally:
                    await blob_service_client.close()
            except Exception as blober:
                raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail = f"Problem in fetching previous data: {str(blober)}")

    async def download_twb_file_from_blob(self,
                            blob_key: str,
                            local_download_path: str) -> list[str]:
            """
            Download a .twb file from Blob to a local path.

            Parameters
            ----------
            blob_key : str
                The Blob object key of the .twb file to download.
            local_download_path : str
                The local directory where the file should be saved.

            Returns
            -------
            List containing the local file path of the downloaded file.
            """

            try:
                try:
                    local_dir = Path(local_download_path)
                    local_dir.mkdir(parents=True, exist_ok=True)
            
                    # Extract the file name from the input path
                    file_name = Path(blob_key).name
                    local_file_path = local_dir / file_name

                    blob_service_client = self.get_blob_client()
                    blob_client = blob_service_client.get_blob_client(
                        container=self.container_name, 
                        blob=blob_key
                    )
                    try:
                        # Download the file from Blob to the local path
                        async with aiofiles.open(local_file_path, 'wb') as local_file:
                            download_stream = await blob_client.download_blob()
                            async for chunk in download_stream.chunks():
                                await local_file.write(chunk)
                        return [str(local_file_path)]
                    except Exception as error:
                        logger.exception(f"Blob download error: {error}")
                        raise HTTPException(
                            status_code=HTTP_STATUS_INTERNAL_ERROR,
                            detail=MSG_S3_DOWNLOAD_FAILED
                        )
                finally:
                    await blob_service_client.close()
            except Exception as blob_error:
                logger.exception(f"Local setup error: {blob_error}")
                raise HTTPException(status_code = HTTP_STATUS_INTERNAL_ERROR,
                                    detail = MSG_S3_FETCH_ERROR)
            

    async def download_semantic_model_input_files(
        self,
        blob_input_prefix: str,
        local_download_path: str,
        allowed_extensions: List[str] = [".twb", ".csv", ".xlsx"]
    ) -> List[str]:
        """
        Downloads all semantic model input files (filtered by extension) from a given Blob prefix to local path.

        Args:
            blob_input_prefix (str): The Blob folder/prefix (e.g., org/email/process_id/input_files)
            local_download_path (str): Local path to store the files.
            allowed_extensions (List[str], optional): File types to download. Defaults to common types.

        Returns:
            List[str]: List of downloaded local file paths.
        """
        try:
            try:
                os.makedirs(local_download_path, exist_ok=True)
                downloaded_files = []

                blob_service_client = self.get_blob_client()
                container_client = blob_service_client.get_container_client(self.container_name)
                
                blob_list = container_client.list_blobs(name_starts_with=blob_input_prefix.rstrip("/") + "/")
                blob_files = list(blob_list)

                if not blob_files:
                    logger.warning(f"No files found at Blob prefix: {blob_input_prefix}")
                    return []

                for blob in blob_files:
                    file_key = blob.name
                    file_name = os.path.basename(file_key)

                    # Skip if not a file or if the extension isn't allowed
                    if not file_name or (allowed_extensions and Path(file_name).suffix.lower() not in allowed_extensions):
                        continue

                    local_file_path = os.path.join(local_download_path, file_name)

                    try:
                        # Stream download to local
                        blob_client = blob_service_client.get_blob_client(
                            container=self.container_name, 
                            blob=file_key
                        )
                        async with aiofiles.open(local_file_path, "wb") as f:
                            download_stream = await blob_client.download_blob()
                            async for chunk in download_stream.chunks():
                                await f.write(chunk)
                        downloaded_files.append(local_file_path)
                        logger.info(f"Downloaded {file_key} to {local_file_path}")

                    except Exception as e:
                        logger.error(f"Failed to download {file_key}: {e}")

                return downloaded_files
            finally:
                await blob_service_client.close()
        except Exception as err:
            logger.exception(f"Failed to download semantic input files from {blob_input_prefix}: {err}")
            raise HTTPException(status_code=500, detail="Failed to download semantic model input files from Blob")
    
    async def copy_all_folder_files_to_local_path(
        self,
        blob_folder_key: str,
        local_path_for_copy: str
    ):
        """
            Downloads all files (from all folders recursively) within the given blob folder prefix
            to the specified local directory, preserving filenames (flattened).
        """
        downloaded_files = []
        try:
            try:
                os.makedirs(local_path_for_copy, exist_ok=True)
                blob_service_client = self.get_blob_client()
                container_client = blob_service_client.get_container_client(self.container_name)

                blob_files = []
                async for blob in container_client.list_blobs(name_starts_with=blob_folder_key.rstrip("/") + "/"):
                    blob_files.append(blob)

                if not blob_files:
                    logger.warning(f"No files found in Blob folder: {blob_folder_key}")
                    return []
                for blob in blob_files:
                    file_key = blob.name
                    file_name = os.path.basename(file_key)
                    local_file_path = os.path.join(local_path_for_copy, file_name)

                    try:
                        await self.download_file(file_key, local_file_path)
                        downloaded_files.append(local_file_path)
                        logger.info(f"Copied {file_key} to {local_file_path}")
                    except Exception as e:
                        logger.error(f"Failed to download {file_key} from blob: {e}")

                return downloaded_files
            finally:
                await blob_service_client.close()

        except Exception as e:
            logger.error(f"Error copying files from blob folder {blob_folder_key}: {e}")
            raise HTTPException(status_code=500, detail="Error occured in Images downloading to the local path")



class OpenAIConfig(BaseSettings):
    api_key: str = os.getenv("OPENAI_API_KEY")
    model_name: str = os.getenv("OPEN_API_MODEL_NAME", "gpt-4o")
    fallback_model: str = os.getenv("OPEN_API_FALLBACK_MODEL", "gpt-4")

    def get_openai_client(self):
        return OpenAI(api_key=self.api_key)
    

class AzureOpenAIConfig(BaseSettings):
    api_key: str = os.getenv("AZURE_OPENAI_API_KEY")
    api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    azure_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    fallback_deployment: str = os.getenv("AZURE_OPENAI_FALLBACK_DEPLOYMENT", "gpt-4")

    def get_openai_client(self):
        return AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )


class DBConfig:
    db_uri = os.getenv("DB_URI")

    @classmethod
    def get_engine(cls):
        return create_engine(cls.db_uri)


class JWTConfig(BaseSettings):
    secret_key: str = os.getenv("JWT_SECRET_KEY")
    algorithm: str = "HS256"


ACCESS_TOKEN_EXPIRY = int(os.getenv("ACCESS_TOKEN_EXPIRY", 500))  # in minutes
REFRESH_TOKEN_EXPIRY = int(os.getenv("REFRESH_TOKEN_EXPIRY", 60 * 3)) # in minutes


class TableauConfig(BaseSettings):
    server_url: str = os.getenv("TABLEAU_SERVER_URL")
    token_name: str = os.getenv("TABLEAU_TOKEN_NAME")
    token_value: str = os.getenv("TABLEAU_TOKEN_VALUE")
    site_name: str = os.getenv("TABLEAU_SITE_NAME")

    def get_tableau_auth(self):
        """
        Returns a Tableau Server Client Auth object
        """
        return TSC.PersonalAccessTokenAuth(
            token_name=self.token_name,
            personal_access_token=self.token_value,
            site_id=self.site_name
        )

    def get_tableau_server(self):
        """
        Returns a connected Tableau Server object
        """
        auth = self.get_tableau_auth()
        server = TSC.Server(self.server_url, use_server_version=True)
        server.auth.sign_in(auth)
        return server

