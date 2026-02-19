import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, cast, text, or_, case, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Query, joinedload
from app.core.session import Base,scoped_context
from app.models.base import AuditMixin
from app.models.users import User, Role
from app.core.session import scoped_context, Base
from app.core.enums import RoleEnum
from sqlalchemy.orm import joinedload
import re


class ProjectDetail(Base, AuditMixin):
    __tablename__ = "project_details"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    is_upload = Column(Boolean, server_default=text("false"), nullable=False)

    site_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.tableau_site_details.id"), nullable=True)
    server_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.tableau_server_details.id"), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.project_details.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.users.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("biporttest.users.id"), nullable=True)

    creator = relationship("User", foreign_keys=[user_id], back_populates="created_projects")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_projects")
    reports = relationship("ReportDetail", back_populates="project")

    @staticmethod
    def get_projects_by_user_role(session, user, role_name: str) -> Query:
        """
        Return a SQLAlchemy query for projects based on user's role and organization.
        """
        query = session.query(ProjectDetail).options(joinedload(ProjectDetail.reports))

        # Filter by organization
        query = query.join(ProjectDetail.creator).filter(User.organization_id == user.organization_id)

        #Role-based access control
        if role_name == "Admin":
            pass  # See all
        elif role_name == "Manager":
            subordinate_ids = session.query(User.id).filter(User.manager_id == user.id).all()
            subordinate_ids = [sid[0] for sid in subordinate_ids]
            query = query.filter(
                or_(
                    ProjectDetail.assigned_to == user.id,
                    ProjectDetail.assigned_to.in_(subordinate_ids)
                )
            )
        elif role_name == "Developer":
            query = query.filter(ProjectDetail.assigned_to == user.id)

        return query
        


class ProjectDetailManager:
    @staticmethod
    def get_all_root_projects(page: int, page_size: int, organization_id: UUID):
        from app.models.report_details import ReportDetail  
        from app.models.users import User as UserModel
        from sqlalchemy.orm import aliased
        offset = (page - 1) * page_size
        with scoped_context() as session:
            # Create aliases for different User joins
            CreatorUser = aliased(UserModel)
            AssignedUser = aliased(UserModel)
            
            return (
                session.query(ProjectDetail, AssignedUser)
                .join(CreatorUser, ProjectDetail.user_id == CreatorUser.id)  # Join with creator to get organization
                .outerjoin(AssignedUser, ProjectDetail.assigned_to == AssignedUser.id)  # Outer join with assigned user
                .filter(
                    ProjectDetail.is_upload == True,
                    ProjectDetail.parent_id == None,
                    ProjectDetail.is_deleted == False,
                    CreatorUser.organization_id == organization_id  # Filter by organization
                )
                .order_by(ProjectDetail.created_at.desc()) 
                .offset(offset)
                .limit(page_size)
                .all()
            )

    @staticmethod
    def get_total_all_root_projects(organization_id: UUID) -> int:
        from app.models.users import User as UserModel
        from sqlalchemy.orm import aliased
        with scoped_context() as session:
            # Create alias for User join
            CreatorUser = aliased(UserModel)
            
            return session.query(ProjectDetail).join(
                CreatorUser, ProjectDetail.user_id == CreatorUser.id
            ).filter(
                ProjectDetail.is_upload == True,
                ProjectDetail.parent_id == None,
                ProjectDetail.is_deleted == False,
                CreatorUser.organization_id == organization_id
            ).count()

 
    @staticmethod
    def assign_user_to_project(project_id: UUID, user_id: UUID):
        with scoped_context() as session:
            project = session.query(ProjectDetail).options(
                joinedload(ProjectDetail.assignee)
            ).filter(
                ProjectDetail.id == project_id,
                ProjectDetail.is_deleted == False
            ).order_by(ProjectDetail.created_at.desc()).first()

            if not project:
                return None

            project.assigned_to = user_id
            session.commit()
            session.refresh(project)
            return project

    @staticmethod
    def get_projects_by_site(site_id: UUID):
        from app.models.report_details import ReportDetail
        with scoped_context() as session:
            admin_user = (
                session.query(User)
                .filter(User.role.has(name=RoleEnum.ADMIN.value), User.is_deleted == False)
                .first()
            )
            admin_id = admin_user.id if admin_user else None

            root_projects = (
                session.query(ProjectDetail)
                .filter(
                    ProjectDetail.site_id == site_id,
                    ProjectDetail.parent_id == None,
                    ProjectDetail.is_deleted == False
                )
                .order_by(ProjectDetail.created_at)   
                .all()
            )

            project_ids = [p.id for p in root_projects]

            sub_projects = (
                session.query(ProjectDetail)
                .filter(
                    ProjectDetail.parent_id.in_(project_ids),
                    ProjectDetail.is_deleted == False
                )
                .order_by(ProjectDetail.created_at)   
                .all()
            )

            for rp in root_projects:
                if not rp.assigned_to:
                    rp.assigned_to = admin_id

            for sp in sub_projects:
                if not sp.assigned_to:
                    sp.assigned_to = admin_id

            assigned_user_ids = set()
            for rp in root_projects:
                if rp.assigned_to:
                    assigned_user_ids.add(rp.assigned_to)
            for sp in sub_projects:
                if sp.assigned_to:
                    assigned_user_ids.add(sp.assigned_to)

            reports = (
                session.query(ReportDetail)
                .filter(
                    ReportDetail.project_id.in_([sp.id for sp in sub_projects]),
                    ReportDetail.is_deleted == False
                )
                .all()
            )

            assigned_users = (
                session.query(User)
                .filter(User.id.in_(assigned_user_ids), User.is_deleted == False)
                .all()
            )
            assigned_users_map = {user.id: user for user in assigned_users}

            return root_projects, sub_projects, reports, assigned_users_map
        
    @staticmethod
    def get_projects_by_parent(parent_id: UUID):
        from app.models.report_details import ReportDetail
        with scoped_context() as session:
            admin_user = session.query(User).join(User.role).filter(Role.name == RoleEnum.ADMIN).first()
            admin_id = admin_user.id if admin_user else None

            sub_projects = session.query(
                ProjectDetail.id,
                ProjectDetail.name,
                ProjectDetail.parent_id,
                ProjectDetail.created_at, 
                case(
                    (ProjectDetail.assigned_to == None, admin_id),
                    else_=ProjectDetail.assigned_to
                ).label("assigned_to"),
                case(
                    (ProjectDetail.assigned_to == None, admin_user.name if admin_user else None),
                    else_=User.name
                ).label("assigned_to_name"),
                User.role_id.label("role_id"),
                User.manager_id.label("manager_id")
            ).outerjoin(User, User.id == ProjectDetail.assigned_to).filter(
                ProjectDetail.parent_id == parent_id,
                ProjectDetail.is_deleted == False
            ).order_by(ProjectDetail.created_at.desc()).all()

            sub_project_ids = [sp.id for sp in sub_projects]

            reports = []
            if sub_project_ids:
                reports = session.query(
                    ReportDetail.id,
                    ReportDetail.name,
                    ReportDetail.project_id,
                    ReportDetail.view_count,
                    ReportDetail.created_at  
                ).filter(
                    ReportDetail.project_id.in_(sub_project_ids),
                    ReportDetail.is_deleted == False
                ).order_by(ReportDetail.created_at.desc()).all()

            return sub_projects, reports


    # @staticmethod
    # def soft_delete_by_server_id(server_id):
    #     from app.models.project_details import ProjectDetail
    #     from app.core.session import scoped_context
    #     with scoped_context() as session:
    #         session.query(ProjectDetail).filter_by(server_id=server_id).update({"is_deleted": True})
    #         session.commit()

    @staticmethod
    def soft_delete_by_server_id(server_id):
        """
        Hard deletes all projects for a server.
        """
        from app.models.project_details import ProjectDetail
        from app.core.session import scoped_context

        with scoped_context() as session:
            projects = session.query(ProjectDetail.id).filter(ProjectDetail.server_id == server_id).all()
            for (project_id,) in projects:
                ProjectDetailManager.soft_delete_project_and_children(project_id)


    @staticmethod
    def get_ids_by_server_id(server_id):
        from app.models.project_details import ProjectDetail
        from app.core.session import scoped_context
        with scoped_context() as session:
            return [p.id for p in session.query(ProjectDetail).filter_by(server_id=server_id).all()]

    @staticmethod
    def get_root_projects_by_user_id(user_id: uuid.UUID, offset: int = 0, limit: int = 10):
        with scoped_context() as session:
            return session.query(ProjectDetail).filter(
                ProjectDetail.user_id == user_id,
                ProjectDetail.parent_id == None,
                ProjectDetail.is_deleted == False,
                ProjectDetail.is_upload == True
            ).order_by(ProjectDetail.updated_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_total_root_projects_by_user_id(user_id: uuid.UUID) -> int:
        with scoped_context() as session:
            return session.query(ProjectDetail).filter(
                ProjectDetail.user_id == user_id,
                ProjectDetail.parent_id == None,
                ProjectDetail.is_deleted == False,
                ProjectDetail.is_upload == True
            ).count()

    @staticmethod
    def get_projects_by_parent_and_user_id(parent_id: uuid.UUID, user_id: uuid.UUID, offset: int = 0, limit: int = 10):
        with scoped_context() as session:
            return session.query(ProjectDetail).filter(
                ProjectDetail.user_id == user_id,
                ProjectDetail.parent_id == parent_id,
                ProjectDetail.is_deleted == False,
                ProjectDetail.is_upload == True
            ).order_by(ProjectDetail.updated_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_total_projects_by_parent_and_user_id(parent_id: uuid.UUID, user_id: uuid.UUID) -> int:
        with scoped_context() as session:
            return session.query(ProjectDetail).filter(
                ProjectDetail.user_id == user_id,
                ProjectDetail.parent_id == parent_id,
                ProjectDetail.is_deleted == False,
                ProjectDetail.is_upload == True
            ).count()

    @staticmethod
    def is_duplicate_project(name: str, user_id: uuid.UUID, parent_id: uuid.UUID = None) -> bool:
        with scoped_context() as session:
            query = session.query(ProjectDetail).filter(
                ProjectDetail.name == name,
                ProjectDetail.user_id == user_id,
                ProjectDetail.is_deleted == False
            )
            if parent_id is None:
                query = query.filter(ProjectDetail.parent_id == None)
            else:
                query = query.filter(ProjectDetail.parent_id == parent_id)
            return session.query(query.exists()).scalar()

    @staticmethod
    def is_duplicate_project_exclude_id(name: str, user_id: uuid.UUID, parent_id: uuid.UUID = None, exclude_id: uuid.UUID = None) -> bool:
        with scoped_context() as session:
            query = session.query(ProjectDetail).filter(
                ProjectDetail.name == name,
                ProjectDetail.user_id == user_id,
                ProjectDetail.is_deleted == False
            )
            if parent_id is None:
                query = query.filter(ProjectDetail.parent_id == None)
            else:
                query = query.filter(ProjectDetail.parent_id == parent_id)
            if exclude_id is not None:
                query = query.filter(ProjectDetail.id != exclude_id)
            return session.query(query.exists()).scalar()

    @staticmethod
    def update_project_name(project_id: uuid.UUID, new_name: str, updated_by: uuid.UUID):
        with scoped_context() as session:
            project = session.query(ProjectDetail).filter(ProjectDetail.id == project_id).first()
            if not project:
                return None
            project.name = new_name
            project.updated_by = updated_by
            session.commit()
            session.refresh(project)
            return project

    @staticmethod
    def get_project_by_id(project_id: uuid.UUID):
        with scoped_context() as session:
            return session.query(ProjectDetail).filter(ProjectDetail.id == project_id).first()


    def add_project(id, name, site_id, server_id, user_id, parent_id=None,created_by=None, updated_by=None, is_upload=False):
        from app.models.project_details import ProjectDetail
        from app.core.session import scoped_context
        with scoped_context() as session:
            project = ProjectDetail(
                id=id,
                name=name,
                site_id=site_id,
                server_id=server_id,
                user_id=user_id,
                parent_id=parent_id if parent_id is not None else None,
                created_by=created_by,
                updated_by=updated_by,
                is_upload=is_upload
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            return project         
 

    @staticmethod
    def add_folder(id, name, user_id, parent_id=None, created_by=None, updated_by=None, is_upload=False, session=None):
        from app.models.project_details import ProjectDetail
        from app.core.session import scoped_context
        if session is None:
            with scoped_context() as session:
                project = ProjectDetail(
                    id=id,
                    name=name,
                    site_id=None,
                    server_id=None,
                    user_id=user_id,
                    parent_id=parent_id if parent_id is not None else None,
                    created_by=created_by,
                    updated_by=updated_by,
                    is_upload=is_upload
                )
                session.add(project)
                session.commit()
                session.refresh(project)
                return project
        else:
            project = ProjectDetail(
                id=id,
                name=name,
                site_id=None,
                server_id=None,
                user_id=user_id,
                parent_id=parent_id if parent_id is not None else None,
                created_by=created_by,
                updated_by=updated_by,
                is_upload=is_upload
            )
            session.add(project)
            session.flush()
            session.refresh(project)
            return project

    # @staticmethod
    # def soft_delete_project_and_children(project_id):
    #     from app.models.project_details import ProjectDetail
    #     from app.models.report_details import ReportDetail
    #     from app.core.session import scoped_context
    #     with scoped_context() as session:
    #         # Recursively find all child projects
    #         def get_all_descendant_project_ids(pid):
    #             ids = [pid]
    #             children = session.query(ProjectDetail.id).filter(ProjectDetail.parent_id == pid, ProjectDetail.is_deleted == False).all()
    #             for (child_id,) in children:
    #                 ids.extend(get_all_descendant_project_ids(child_id))
    #             return ids
    #         all_project_ids = get_all_descendant_project_ids(project_id)
    #         # Soft delete all projects
    #         session.query(ProjectDetail).filter(ProjectDetail.id.in_(all_project_ids)).update({"is_deleted": True}, synchronize_session=False)
    #         # Soft delete all reports under these projects
    #         session.query(ReportDetail).filter(ReportDetail.project_id.in_(all_project_ids)).update({"is_deleted": True}, synchronize_session=False)
    #         session.commit()

    @staticmethod
    def soft_delete_project_and_children(project_id,org_name):
        """
        Hard deletes a project, all child projects, and their reports (with S3 archive).
        """
        from app.models.project_details import ProjectDetail
        from app.models.report_details import ReportDetail, ReportDetailManager
        from app.core.session import scoped_context

        with scoped_context() as session:

            # Recursively get all descendant project IDs
            def get_all_descendant_project_ids(pid):
                ids = [pid]
                children = session.query(ProjectDetail.id).filter(ProjectDetail.parent_id == pid).all()
                for (child_id,) in children:
                    ids.extend(get_all_descendant_project_ids(child_id))
                return ids

            all_project_ids = get_all_descendant_project_ids(project_id)

            # Delete reports for all these projects using centralized report hard delete
            reports = session.query(ReportDetail).filter(ReportDetail.project_id.in_(all_project_ids)).all()
            for report in reports:
                ReportDetailManager.soft_delete_report(report.id,org_name)  # calls S3 archive + deletion

            # Delete the projects
            session.query(ProjectDetail).filter(ProjectDetail.id.in_(all_project_ids)).delete(synchronize_session=False)
            session.commit()

    @staticmethod
    async def process_zip_upload(extract_dir, project_id, filename, user, org_name, cloud_storage, cloud_provider, ReportDetailManager, twbx_extractor=None):
        import os
        from fastapi import HTTPException
        import uuid as uuidlib
        from app.core.session import scoped_context
        with scoped_context() as session:
            async def process_folder(abs_path, parent_project_id, rel_path):
                folder_name = os.path.basename(abs_path)
                if rel_path == '':
                    project_name = os.path.splitext(filename)[0]
                else:
                    project_name = folder_name
                if ProjectDetailManager.is_duplicate_project(project_name, user.id, parent_id=parent_project_id):
                    raise HTTPException(status_code=409, detail=f"Project '{project_name}' already exists.")
                project = ProjectDetailManager.add_folder(
                    id=uuidlib.uuid4(),
                    name=project_name,
                    user_id=user.id,
                    parent_id=parent_project_id,
                    created_by=user.id,
                    updated_by=user.id,
                    is_upload=True,
                    session=session
                )
                for entry in os.listdir(abs_path):
                    entry_path = os.path.join(abs_path, entry)
                    entry_rel_path = os.path.join(rel_path, entry) if rel_path else entry
                    if os.path.isdir(entry_path):
                        await process_folder(entry_path, project.id, entry_rel_path)
                    else:
                        if not (entry.endswith('.twb') or entry.endswith('.twbx')):
                            raise HTTPException(status_code=400, detail=f"Invalid file '{entry_rel_path}': only .twb/.twbx files allowed.")
                        
                        def _normalize_name(name: str) -> str:
                            n = name.strip()
                            n = re.sub(r"\s+\.(twb|twbx)$", r".\1", n, flags=re.IGNORECASE)
                            n = re.sub(r"\s+", " ", n)
                            return n
                        normalized_entry = _normalize_name(entry)

                        if ReportDetailManager.is_duplicate_report(normalized_entry, project.id, user.id):
                            continue
                        # Extract file extension for report type (only for Tableau files)
                        # file_ext = os.path.splitext(entry)[1].lower().replace('.', '')
                        file_ext = os.path.splitext(normalized_entry)[1].lower().replace('.', '')

                        report_type = file_ext if file_ext in ['twb', 'twbx'] else None
                        report = ReportDetailManager.add_report(
                            id=uuidlib.uuid4(),
                            name=normalized_entry,
                            report_id=str(uuidlib.uuid4()),
                            project_id=project.id,
                            created_by=user.id,
                            updated_by=user.id,
                            report_type=report_type,
                            session=session
                        )
                        cloud_path = f"BI-Portfinal/{org_name}/{report.report_id}/tableau_file/{normalized_entry}"
                        if cloud_provider == "azure":
                            await cloud_storage.upload_to_blob(file_path=entry_path, object_name=cloud_path)
                        else:
                            await cloud_storage.upload_to_s3(file_path=entry_path, object_name=cloud_path)

                        # Check if it's a TWBX file and extract its contents
                        if entry.endswith('.twbx') and twbx_extractor:
                            await twbx_extractor(entry_path, org_name, report.report_id, cloud_storage)
                return project
            await process_folder(extract_dir, project_id, '')
            session.commit()
    
    @staticmethod
    def get_sub_projects_with_reports(parent_ids: list[UUID]):
        from app.models.report_details import ReportDetail
        with scoped_context() as session:
            admin_user = session.query(User).join(User.role).filter(Role.name == RoleEnum.ADMIN).first()
            admin_id = admin_user.id if admin_user else None
            admin_name = admin_user.name if admin_user else "Admin"

            projects = session.query(
                ProjectDetail.id,
                ProjectDetail.name,
                ProjectDetail.parent_id,
                case(
                    (ProjectDetail.assigned_to == None, admin_id),
                    else_=ProjectDetail.assigned_to
                ).label("assigned_to"),
                case(
                    (ProjectDetail.assigned_to == None, admin_name),
                    else_=User.name
                ).label("assigned_to_name"),
                case(
                    (ProjectDetail.assigned_to == None, admin_user.role_id if admin_user else None),
                    else_=User.role_id
                ).label("role_id"),
                case(
                    (ProjectDetail.assigned_to == None, admin_user.manager_id if admin_user else None),
                    else_=User.manager_id
                ).label("manager_id")
            ).outerjoin(User, User.id == ProjectDetail.assigned_to).filter(
                ProjectDetail.parent_id.in_(parent_ids),
                ProjectDetail.is_deleted == False
            ).all()

            project_ids = [p.id for p in projects] + parent_ids

            reports = session.query(
                ReportDetail.id,
                ReportDetail.name,
                ReportDetail.project_id,
                ReportDetail.view_count
            ).filter(
                ReportDetail.project_id.in_(project_ids),
                ReportDetail.is_deleted == False
            ).all()

            return projects, reports
        
    @staticmethod
    def search_by_keyword_filtered(keyword: str, org_id: str):
        """
        Returns all projects matching keyword (in project or report name)
        and owned by users in the given org.
        """
        from app.models.report_details import ReportDetail
        keyword = f"%{keyword.strip()}%"

        with scoped_context() as session:
            matched_projects = session.query(ProjectDetail).options(
                joinedload(ProjectDetail.reports)
            ).join(
                ReportDetail, isouter=True
            ).join(
                User, ProjectDetail.user_id == User.id
            ).filter(
                or_(
                    ProjectDetail.name.ilike(keyword),
                    ReportDetail.name.ilike(keyword)
                ),
                User.organization_id == org_id 
            ).all()
            return matched_projects

    @staticmethod
    def get_projects_by_ids(project_ids: list[UUID]) -> list[ProjectDetail]:
        with scoped_context() as session:
            return session.query(ProjectDetail).options(
                joinedload(ProjectDetail.reports)
            ).filter(
                ProjectDetail.id.in_(project_ids)
            ).all()

    @staticmethod
    def get_projects_hierarchy_by_keyword(keyword: str, org_id: str):
        """
        Returns all projects matching the keyword (in project or report name),
        owned by users in the given org, and builds their parent/child hierarchy.
        """
        matched_projects = ProjectDetailManager.search_by_keyword_filtered(keyword.strip(), org_id)
        matched_project_ids = {p.id for p in matched_projects}
        child_map = {}
        all_projects = {}
        to_process = list(matched_project_ids)

        while to_process:
            parents = ProjectDetailManager.get_projects_by_ids(to_process)
            next_batch = []

            for proj in parents:
                if proj.id not in all_projects:
                    all_projects[proj.id] = proj
                    if proj.parent_id:
                        next_batch.append(proj.parent_id)
                    child_map.setdefault(proj.parent_id, []).append(proj)

            to_process = next_batch
        return all_projects, child_map
    
    @staticmethod
    def get_assigned_user_for_project(project_user_id: str) -> dict:
        """
        Given a project user_id, fetch the user details including role and manager.
        Returns a dict with user info or empty dict if user not found.
        """
        from app.models.users import UserManager

        with scoped_context() as session:
            user = UserManager.get_user_by_id_with_relations(project_user_id, session)
            if not user:
                return {}

            return {
                "id": str(user.id),
                "assigned_user": user.name,
                "role_id": str(user.role_id),
                "manager_id": str(user.manager_id) if user.manager_id else None,
            }

    @staticmethod
    def get_project_inventory_by_org(org_id: UUID) -> list[dict]:
        """
        Fetch root projects for an organization with total report count.
        Aggregates reports from all nested sub-projects (any level) into their root.
        Only root projects (parent_id is NULL) are returned.
        """
        with scoped_context() as session:
            # 1. Fetch all projects for this org
            all_projects = (
                session.query(ProjectDetail)
                .join(User, ProjectDetail.user_id == User.id)
                .filter(
                    User.organization_id == org_id,
                    ProjectDetail.is_deleted == False
                )
                .all()
            )

            # 2. Build parent -> children mapping
            children_map = {}
            for p in all_projects:
                if p.parent_id:
                    children_map.setdefault(p.parent_id, []).append(p.id)

            # 3. Fetch all report counts
            from app.models.report_details import ReportDetail
            report_counts = (
                session.query(
                    ReportDetail.project_id,
                    func.count(ReportDetail.id).label("report_count")
                )
                .filter(
                    ReportDetail.project_id.in_([p.id for p in all_projects]),
                    ReportDetail.is_deleted == False
                )
                .group_by(ReportDetail.project_id)
                .all()
            )
            report_count_map = {r.project_id: r.report_count for r in report_counts}

            # 4. Recursive function to sum reports for a project and all descendants
            def total_reports(project_id):
                total = report_count_map.get(project_id, 0)
                for child_id in children_map.get(project_id, []):
                    total += total_reports(child_id)
                return total

            # 5. Prepare inventory for root projects only
            inventory = []
            for p in all_projects:
                if p.parent_id is None:
                    inventory.append({
                        "project_id": str(p.id),
                        "project_name": p.name,
                        "report_count": total_reports(p.id)
                    })
            return inventory