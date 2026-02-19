import os
import json
import uuid
import asyncio
import aiofiles

from app.models_old.site_discovery import SiteDiscoveryManager, DiscoverSiteStatus
from app.core.constants import (
    LOCAL_DIR, FILE_TYPE, MAX_UPLOAD_RETRIES, RETRY_BACKOFF_BASE,
    CLOUD_SITE_DISCOVERY_DIR
)
from app.models_old.cloud_server import CloudServerDetailsManager
from app.models_old.server import ServerDetailsManager
from app.core.config import S3Config, logger

class SiteDiscoveryService:
    def __init__(
        self,
        server_url: str,
        server_id: uuid.UUID,
        server_type_id: uuid.UUID,
        site_discovery_id: uuid.UUID = None,
        pat_name: str = "",
        pat_secret: str = ""
    ):
        os.makedirs(LOCAL_DIR, exist_ok=True)

        self.server_url = server_url
        self.server_id = server_id
        self.site_discovery_id = site_discovery_id
        self.server_type_id = server_type_id
        self.pat_name = pat_name
        self.pat_secret = pat_secret

        # self.s3 = S3Config()
        cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower().strip()
        if cloud_provider == "azure":
            from app.core.config import BlobConfig
            self.cloud_storage = BlobConfig()
            self.cloud_provider = "azure"
        else:
            from app.core.config import S3Config
            self.cloud_storage = S3Config()
            self.cloud_provider = "aws"
        self.site_discovery_manager = SiteDiscoveryManager()
        self.csd_manager = CloudServerDetailsManager
        self.server_details_manager = ServerDetailsManager

        self.local_path = os.path.join(LOCAL_DIR, f"{server_id}_{server_type_id}.{FILE_TYPE}")
        self.cloud_path = f"{CLOUD_SITE_DISCOVERY_DIR}{server_id}.{FILE_TYPE}"

        self.summary_local_path = os.path.join(
            LOCAL_DIR, f"{server_id}_{server_type_id}_projects.{FILE_TYPE}"
        )

    async def _download_file_if_exists(self, object_path: str, local_path: str) -> list:
        if await self.cloud_storage.check_file_exists(object_path):
            await self.cloud_storage.download_file(object_path, local_path)
            async with aiofiles.open(local_path, mode="r") as f:
                content = await f.read()
            try:
                existing_data = json.loads(content)
                if isinstance(existing_data, list):
                    return existing_data
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse {object_path}, overwriting with new data.")
        return []

    async def _upload_file_with_retries(self, local_path: str, object_path: str) -> bool:
        for attempt in range(1, MAX_UPLOAD_RETRIES + 1):
            if self.cloud_provider == "azure":
                success = await self.cloud_storage.upload_to_blob(file_path=local_path, object_name=object_path)
            else:
                success = await self.cloud_storage.upload_to_s3(file_path=local_path, object_name=object_path)
            if success:
                return True
            wait_time = RETRY_BACKOFF_BASE ** attempt
            logger.warning(f"S3 upload failed (attempt {attempt}), retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
        return False

    async def _process_json_file_upload(self, data: list, cloud_path: str, local_path: str) -> None:
        existing_data = await self._download_file_if_exists(cloud_path, local_path)
        combined_data = existing_data + data

        async with aiofiles.open(local_path, mode="w") as f:
            await f.write(json.dumps(combined_data, indent=4))

        if not await self._upload_file_with_retries(local_path, cloud_path):
            logger.error(f"Failed to upload {cloud_path} to cloud storage.")

        if os.path.exists(local_path):
            os.remove(local_path)

    async def _discover_site(self) -> dict:
        from app.services import TableauClient
        
        client = TableauClient(self.server_id, self.server_url, self.pat_name, self.pat_secret)
        site_data = await client.get_site_data()
        project_summary = site_data.pop("project_summary", [])

        if project_summary:
            self.csd_manager.update_project_summary(
                cloud_server_id=self.server_type_id,
                summary_data=project_summary
            )
        self.server_details_manager.update_project_and_report_count(
            server_id=self.server_id,
            project_count=len(site_data.get("projects", [])),
            report_count=site_data.get("workbooks_count", 0)
        )
        site_usage = 0
        for project in site_data.get("projects", []):
            client.calculate_usage(project)
            site_usage += project.get("usage", 0)

        site_data.update({
            "usage": site_usage,
            "server_id": str(self.server_id)
        })
        return site_data

    async def run(self) -> None:
        try:
            self.site_discovery_manager.update(id=self.site_discovery_id, status=DiscoverSiteStatus.STARTED)

            site_data = await self._discover_site()
            await self._process_json_file_upload([site_data], self.cloud_path, self.local_path)

            self.site_discovery_manager.update(id=self.site_discovery_id, status=DiscoverSiteStatus.COMPLETED)
            logger.info("Site discovery completed successfully.")
        except Exception as e:
            logger.error(f"Site discovery failed: {e}")
            self.site_discovery_manager.update(id=self.site_discovery_id, status=DiscoverSiteStatus.FAILED)
        finally:
            if os.path.exists(self.local_path):
                os.remove(self.local_path)
