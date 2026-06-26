# Built-in Dependencies
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_origin,
    get_args,
)
from datetime import datetime, UTC

# Third-Party Dependencies
from sqlmodel import select, update, delete, func, and_, or_, inspect
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import asc, desc, Select, Column
from sqlalchemy.engine.row import Row
from sqlalchemy.sql import Join
from sqlmodel import SQLModel

# Local Dependencies
from src.core.utils.repository import (
    _extract_matching_columns_from_schema,
    _extract_matching_columns_from_kwargs,
    _auto_detect_join_condition,
    _add_column_with_prefix,
)
from src.core.common.models import Base
from src.core.config import settings

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)
UpdateSchemaInternalType = TypeVar("UpdateSchemaInternalType", bound=SQLModel)
DeleteSchemaType = TypeVar("DeleteSchemaType", bound=SQLModel)


class RepositoryBase(
    Generic[
        ModelType,
        CreateSchemaType,
        UpdateSchemaType,
        UpdateSchemaInternalType,
        DeleteSchemaType,
    ]
):
    """
    Base class for repository operations on a model.

    Parameters
    ----------
    model : Type[ModelType]
        The SQLAlchemy model type.
    """

    def __init__(self, model: Type[ModelType]) -> None:
        self._model = model

    def apply_filtering(self, stmt, use_or: bool = False, **kwargs):
        """
        Apply filtering to the SQL query based on the provided filters.
        Uses 'ilike' for string fields and equality for other types.

        Parameters
        ----------
        stmt : select
            The SQLAlchemy select statement to apply filtering on.
        use_or : bool
            If True, combine filters using OR instead of AND.
        kwargs : dict
            Filters to apply to the query.

        Returns
        -------
        select
            The SQLAlchemy select statement with filtering applied.
        """
        filters = []
        for field_name, value in kwargs.items():
            # Check if the field exists in the Pydantic model schema
            field_info = self._model.model_fields.get(field_name)
            if field_info:
                column = getattr(self._model, field_name, None)
                field_type = field_info.annotation  # Retrieve the field type

                # Check if the field type is a string or a Union of strings
                is_string = field_type is str or (
                    get_origin(field_type) is Union and str in get_args(field_type)
                )

                # Apply 'ilike' filter for string fields, otherwise use equality
                if is_string:
                    filters.append(column.ilike(f"%{value}%"))
                else:
                    filters.append(column == value)

        # Apply the filters using AND or OR based on the 'use_or' flag
        if filters:
            stmt = stmt.filter(or_(*filters)) if use_or else stmt.filter(and_(*filters))

        # Always remove is_deleted filter if it exists
        if "is_deleted" in self._model.__table__.columns:
            stmt = stmt.filter(self._model.is_deleted == False)

        return stmt

    def apply_json_filters(
        self,
        stmt: Select,
        json_column: Column,
        json_key: Optional[str] = None,
        json_value: Any = None,
        json_contains: Optional[dict] = None,
        json_not_contains: Optional[dict] = None,
    ) -> Select:
        """
        Apply JSON filters to a SQLModel statement.

        Args:
            stmt: The SQLModel select statement
            json_column: The JSON column to apply filters to
            json_key: Key in JSON column to filter by
            json_value: Value to match for the specified json_key
            json_contains: Dict to check if it is contained in JSON column
            json_not_contains: Dict to check if it is NOT contained in JSON column

        Returns:
            The modified statement with JSON filters applied
        """
        # Apply JSON filtering based on json_key and json_value
        if json_key and json_value is not None:
            stmt = stmt.filter(json_column[json_key].astext == str(json_value))

        # Apply JSON filtering based on json_contains
        if json_contains:
            stmt = stmt.filter(json_column.contains(json_contains))

        # Apply JSON filtering based on json_not_contains
        if json_not_contains:
            stmt = stmt.filter(~json_column.contains(json_not_contains))

        return stmt

    def apply_sorting(self, stmt: select, sort_by: List[Tuple[str, str]]) -> select:
        """
        Apply sorting to the SQL query based on the provided sorting criteria.

        Parameters
        ----------
        stmt : select
            The SQLAlchemy select statement to apply sorting on.
        sort_by : List[Tuple[str, str]]
            A list of tuples where each tuple contains a field name and the direction ('asc' or 'desc').

        Returns
        -------
        select
            The SQLAlchemy select statement with sorting applied.
        """
        if sort_by:
            # Get the column names from the current SQL statement
            column_names = [col.name for col in stmt.columns]

            # Create a mapping of column names to their respective tables/models
            column_to_model = {}
            for col_desc in stmt.column_descriptions:
                # Check if "entity" exists in the column description
                entity = col_desc.get("entity")
                column_name = col_desc.get("name")

                if entity is not None and column_name:
                    # Map the column name to its model (entity)
                    column_to_model[column_name] = entity

            # Apply sorting
            order_by_clauses = []
            for field_name, direction in sort_by:
                if field_name in column_names:
                    # Retrieve the actual column from the model class
                    if field_name in column_to_model:
                        column = field_name
                    else:
                        column = getattr(self._model, field_name, None)

                    # Add the order by clause
                    if column is not None:
                        if direction == "asc":
                            order_by_clauses.append(asc(column))
                        elif direction == "desc":
                            order_by_clauses.append(desc(column))
                else:
                    print(f"Warning: Column '{field_name}' not found in columns list.")

            if order_by_clauses:
                stmt = stmt.order_by(*order_by_clauses)

        elif hasattr(self._model, "created_at"):
            stmt = stmt.order_by(self._model.created_at)

        return stmt

    async def create(
        self, db: AsyncSession, object: CreateSchemaType, with_commit: bool = True
    ) -> ModelType:
        """
        Create a new record in the database.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        object : CreateSchemaType
            The SQLModel (Pydantic) schema containing the data to be saved.
        with_commit : bool, optional
            Flag indicating whether to commit the changes to the database.

        Returns
        -------
        ModelType
            The created database object.
        """
        object_dict = object.model_dump()
        db_object: ModelType = self._model(**object_dict)
        db.add(db_object)

        # Commit or flush the changes
        if not with_commit:
            await db.flush()
        else:
            await db.commit()
        return db_object

    async def get(
        self,
        db: AsyncSession,
        schema_to_select: Union[Type[SQLModel], List, None] = None,
        return_object: bool = False,
        return_is_deleted: bool = False,
        **kwargs: Any,
    ) -> Dict | None | Row:
        """
        Fetch a single record based on filters.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        schema_to_select : Union[Type[SQLModel], List, None], optional
            SQLModel (Pydantic) schema for selecting specific columns. Default is None to select all columns.
        return_object : bool, optional
            Flag indicating whether to return the database row object (`Row`) directly instead of a dictionary representation.
        return_is_deleted : bool, optional
            Whether to include soft-deleted records in the query. If ``True``, records marked as deleted are also considered. Defaults to ``False``.
        **kwargs : dict
            Filters to apply to the query.

        Returns
        -------
        dict | Row | None
            The fetched database row as a dictionary or `Row` object, or None if not found. Returns `Row` object if `return_object=True`.
        """
        to_select = _extract_matching_columns_from_schema(
            model=self._model, schema=schema_to_select
        )
        stmt = select(*to_select).filter_by(**kwargs)

        # Always remove is_deleted filter if it exists
        if return_is_deleted == False and "is_deleted" in self._model.__table__.columns:
            stmt = stmt.filter(self._model.is_deleted == False)

        db_row = await db.exec(stmt)
        result: Row = db_row.first()

        # Return the row
        if return_object:
            return result

        # Return the dictionary representation of the row
        if result is not None:
            out: dict = dict(result._mapping)
            return out

        # Return None if there are no result
        return None

    async def get_only_id(
        self,
        db: AsyncSession,
        **kwargs: Any,
    ) -> str | None:
        """
        Fetch the ID of a single record based on filters.

        Optimized for quick ID lookups by selecting only the ID column and handling
        database-specific UUID representations automatically.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        **kwargs : dict
            Filters to apply to the query.

        Returns
        -------
        str | None
            The ID of the record as a string, or None if not found.

        Notes
        -----
        - This method is significantly more efficient than using the generic `get`
        method for ID-only lookups as it avoids unnecessary column processing
        - Automatically handles both raw UUID objects and Row objects from different
        database drivers
        - Always returns ID as a string for consistent application-level handling
        """
        stmt = select(self._model.id).filter_by(**kwargs)

        # Always remove is_deleted filter if it exists
        if "is_deleted" in self._model.__table__.columns:
            stmt = stmt.filter(self._model.is_deleted == False)

        result = await db.scalar(stmt)

        if result is None:
            return None

        # Handle both Row objects and direct UUID representations
        return str(result.id) if hasattr(result, "id") else str(result)

    async def exists(self, db: AsyncSession, **kwargs: Any) -> bool:
        """
        Check if a record exists based on filters.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        kwargs : dict
            Filters to apply to the query.

        Returns
        -------
        bool
            True if a record exists, False otherwise.
        """
        to_select = _extract_matching_columns_from_kwargs(model=self._model, kwargs=kwargs)
        stmt = select(*to_select)

        # Always remove is_deleted filter if it exists
        if "is_deleted" in self._model.__table__.columns:
            stmt = stmt.filter(self._model.is_deleted == False)

        stmt = stmt.filter_by(**kwargs).limit(1)

        result = await db.exec(stmt)
        return result.first() is not None

    async def total_count(
        self, db: AsyncSession, stmt_without_pagination: Optional[select] = None
    ) -> int:
        """
        Retrieve the total number of records that match the applied filters.

        This function executes a count query based on the provided SQLAlchemy
        statement, which should not include pagination.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous database session.
        stmt_without_pagination : Optional[select]
            The SQLAlchemy select statement without offset and limit.

        Returns
        -------
        int
            The total number of records that satisfy the given filters.

        Notes
        -----
        - The query uses a subquery to count the records efficiently.
        - Ensure that `stmt_without_pagination` does not contain `offset` or `limit`, as they would affect the count result.
        """
        # Create a select statement without pagination
        if stmt_without_pagination is None:
            stmt_without_pagination = select(self._model)

        # Always remove is_deleted filter if it exists
        if "is_deleted" in self._model.__table__.columns:
            stmt_without_pagination = stmt_without_pagination.filter(
                self._model.is_deleted == False
            )

        # Create a count query using a subquery to count only filtered records
        count_query = select(func.count()).select_from(stmt_without_pagination.subquery())

        # Execute the count query and retrieve the total number of records
        return await db.scalar(count_query) or 0

    async def get_all(
        self,
        db: AsyncSession,
        sort_by: List[Tuple[str, str]] = None,
        schema_to_select: Union[Type[SQLModel], List[Type[SQLModel]], None] = None,
        return_object: bool = False,
        **kwargs: Any,
    ) -> List[Dict[str, Any]] | List[Row]:
        """
        Fetch all records based on filters.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        sort_by : List[Tuple[str, str]]
            A list of tuples where each tuple contains a field name and the direction ('asc' or 'desc').
        schema_to_select : Union[Type[SQLModel], List[Type[SQLModel]], None], optional
            SQLModel (Pydantic) schema for selecting specific columns. Default is None to select all columns.
        return_object : bool, optional
            Flag indicating whether to return the database row object (`Row`) directly instead of a dictionary representation.
        kwargs : dict
            Filters to apply to the query.

        Returns
        -------
        List[Dict[str, Any]] / List[Row]
            List of dictionaries or objects containing the fetched rows.
        """
        # Extract matching columns from the schema or select all
        to_select = _extract_matching_columns_from_schema(
            model=self._model, schema=schema_to_select
        )
        stmt = select(*to_select)

        # Always remove is_deleted filter if it exists
        if "is_deleted" in self._model.__table__.columns:
            stmt = stmt.filter(self._model.is_deleted == False)

        stmt = stmt.filter_by(**kwargs)

        # Apply sorting if provided
        stmt = self.apply_sorting(stmt, sort_by)

        # Execute the query and map the results
        result = await db.exec(stmt)

        # Return the results
        if return_object:
            return result

        # Convert the results to a list of dictionaries
        if result is not None:
            data = [dict(row) for row in result.mappings()]
            return data

        # Return an empty list if there are no results
        return []

    async def get_multi(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 100,
        sort_by: List[Tuple[str, str]] = None,
        schema_to_select: Union[Type[SQLModel], List[Type[SQLModel]], None] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Fetch multiple records based on filters.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        offset : int, optional
            Number of rows to skip before fetching. Default is 0.
        limit : int, optional
            Maximum number of rows to fetch. Default is 100.
        sort_by : List[Tuple[str, str]]
            A list of tuples where each tuple contains a field name and the direction ('asc' or 'desc').
        schema_to_select : Union[Type[SQLModel], List[Type[SQLModel]], None], optional
            SQLModel (Pydantic) schema for selecting specific columns. Default is None to select all columns.
        kwargs : dict
            Filters to apply to the query.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing the fetched rows under 'data' key and total count under 'total_count'.
        """
        to_select = _extract_matching_columns_from_schema(
            model=self._model, schema=schema_to_select
        )
        stmt = select(*to_select)

        # Apply filtering
        stmt = self.apply_filtering(stmt, **kwargs)

        # Statement without pagination
        stmt_without_pagination = stmt

        # Apply sorting if provided
        stmt = self.apply_sorting(stmt, sort_by)

        # Add pagination
        stmt = stmt.offset(offset).limit(limit)

        result = await db.exec(stmt)
        data = [dict(row) for row in result.mappings()]

        # Get the total count of records matching the query
        total_count: int = await self.total_count(
            db=db, stmt_without_pagination=stmt_without_pagination
        )

        return {"data": data, "total_count": total_count}

    async def get_joined(
        self,
        db: AsyncSession,
        join_model: Type[ModelType],
        join_prefix: str | None = None,
        join_on: Union[Join, None] = None,
        schema_to_select: Union[Type[SQLModel], List, None] = None,
        join_schema_to_select: Union[Type[SQLModel], List, None] = None,
        join_type: str = "left",
        **kwargs: Any,
    ) -> dict | None:
        """
        Fetches a single record with a join on another model. If 'join_on' is not provided, the method attempts
        to automatically detect the join condition using foreign key relationships.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        join_model : Type[ModelType]
            The model to join with.
        join_prefix : Optional[str]
            Optional prefix to be added to all columns of the joined model. If None, no prefix is added.
        join_on : Join, optional
            SQLAlchemy Join object for specifying the ON clause of the join. If None, the join condition is
            auto-detected based on foreign keys.
        schema_to_select : Union[Type[SQLModel], List, None], optional
            SQLModel (Pydantic) schema for selecting specific columns from the primary model.
        join_schema_to_select : Union[Type[SQLModel], List, None], optional
            SQLModel (Pydantic) schema for selecting specific columns from the joined model.
        join_type : str, default "left"
            Specifies the type of join operation to perform. Can be "left" for a left outer join or "inner" for an inner join.
        kwargs : dict
            Filters to apply to the query.

        Returns
        ----------
        Dict | None
            The fetched database row or None if not found.

        Examples
        ----------
        Simple example: Joining User and Tier models without explicitly providing join_on
        ```python
        result = await crud_user.get_joined(
            db=session,
            join_model=Tier,
            schema_to_select=UserSchema,
            join_schema_to_select=TierSchema
        )
        ```

        Complex example: Joining with a custom join condition, additional filter parameters, and a prefix
        ```python
        from sqlalchemy import and_
        result = await crud_user.get_joined(
            db=session,
            join_model=Tier,
            join_prefix="tier_",
            join_on=and_(SystemUser.tier_id == Tier.id, SystemUser.is_superuser == True),
            schema_to_select=UserSchema,
            join_schema_to_select=TierSchema,
            username="john_doe"
        )
        ```

        Return example: prefix added, no schema_to_select or join_schema_to_select
        ```python
        {
            "name": "John Doe",
            "username": "john_doe",
            "email": "johndoe@example.com",
            "hashed_password": "hashed_password_example",
            "profile_image_url": "https://profileimageurl.com/default.jpg",
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-02T12:00:00",
            "deleted_at": null,
            "is_deleted": false,
            "is_superuser": false,
            "tier_id": "123b4566-e89b-12d3-a456-426614174111",
            "tier_name": "Premium",
            "tier_created_at": "2022-12-01T10:00:00",
            "tier_updated_at": "2023-01-01T11:00:00"
        }
        ```
        """
        if join_on is None:
            join_on = _auto_detect_join_condition(self._model, join_model)

        # Extract columns to select from primary model based on schema
        primary_select = _extract_matching_columns_from_schema(
            model=self._model, schema=schema_to_select
        )
        join_select = []

        # Extract columns to select from joined model based on schema or all columns if schema_to_select is not provided
        if join_schema_to_select:
            columns = _extract_matching_columns_from_schema(
                model=join_model, schema=join_schema_to_select
            )
        else:
            columns = inspect(join_model).c

        for column in columns:
            labeled_column = _add_column_with_prefix(column, join_prefix)
            if f"{join_prefix}{column.name}" not in [col.name for col in primary_select]:
                join_select.append(labeled_column)

        # Build the select statement with the specified join type and join condition
        if join_type == "left":
            stmt = select(*primary_select, *join_select).outerjoin(join_model, join_on)
        elif join_type == "inner":
            stmt = select(*primary_select, *join_select).join(join_model, join_on)
        else:
            raise ValueError(f"Invalid join type: {join_type}. Only 'left' or 'inner' are valid.")

        # Apply additional filters based on kwargs
        for key, value in kwargs.items():
            if hasattr(self._model, key):
                stmt = stmt.where(getattr(self._model, key) == value)

        # Always remove is_deleted filter if it exists
        if "is_deleted" in self._model.__table__.columns:
            stmt = stmt.filter(self._model.is_deleted == False)

        # Execute the statement and retrieve the result
        db_row = await db.exec(stmt)
        result: Row = db_row.first()
        if result:
            out: dict = dict(result._mapping)
            return out

        return None

    async def get_multi_joined(
        self,
        db: AsyncSession,
        join_model: Type[ModelType],
        join_prefix: str | None = None,
        join_on: Union[Join, None] = None,
        schema_to_select: Union[Type[SQLModel], List[Type[SQLModel]], None] = None,
        join_schema_to_select: Union[Type[SQLModel], List[Type[SQLModel]], None] = None,
        join_type: str = "left",
        offset: int = 0,
        limit: int = 100,
        sort_by: List[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Fetch multiple records with a join on another model, allowing for pagination.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        join_model : Type[ModelType]
            The model to join with.
        join_prefix : Optional[str]
            Optional prefix to be added to all columns of the joined model. If None, no prefix is added.
        join_on : Join, optional
            SQLAlchemy Join object for specifying the ON clause of the join. If None, the join condition is
            auto-detected based on foreign keys.
        schema_to_select : Union[Type[SQLModel], List[Type[SQLModel]], None], optional
            SQLModel (Pydantic) schema for selecting specific columns from the primary model.
        join_schema_to_select : Union[Type[SQLModel], List[Type[SQLModel]], None], optional
            SQLModel (Pydantic) schema for selecting specific columns from the joined model.
        join_type : str, default "left"
            Specifies the type of join operation to perform. Can be "left" for a left outer join or "inner" for an inner join.
        offset : int, default 0
            The offset (number of records to skip) for pagination.
        limit : int, default 100
            The limit (maximum number of records to return) for pagination.
        sort_by : List[Tuple[str, str]]
            A list of tuples where each tuple contains a field name and the direction ('asc' or 'desc').
        kwargs : dict
            Filters to apply to the primary query.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing the fetched rows under 'data' key and total count under 'total_count'.

        Examples
        --------
        # Fetching multiple User records joined with Tier records, using left join
        users = await crud_user.get_multi_joined(
            db=session,
            join_model=Tier,
            join_prefix="tier_",
            join_on=SystemUser.tier_id == Tier.id,
            schema_to_select=UserSchema,
            join_schema_to_select=TierSchema,
            offset=0,
            limit=10
        )
        """
        if join_on is None:
            join_on = _auto_detect_join_condition(self._model, join_model)

        primary_select = _extract_matching_columns_from_schema(
            model=self._model, schema=schema_to_select
        )
        join_select = []

        if join_schema_to_select:
            columns = _extract_matching_columns_from_schema(
                model=join_model, schema=join_schema_to_select
            )
        else:
            columns = inspect(join_model).c

        for column in columns:
            labeled_column = _add_column_with_prefix(column, join_prefix)
            if f"{join_prefix}{column.name}" not in [col.name for col in primary_select]:
                join_select.append(labeled_column)

        if join_type == "left":
            stmt = select(*primary_select, *join_select).outerjoin(join_model, join_on)
        elif join_type == "inner":
            stmt = select(*primary_select, *join_select).join(join_model, join_on)
        else:
            raise ValueError(f"Invalid join type: {join_type}. Only 'left' or 'inner' are valid.")

        for key, value in kwargs.items():
            if hasattr(self._model, key):
                stmt = stmt.where(getattr(self._model, key) == value)

        # Always remove is_deleted filter if it exists
        if "is_deleted" in self._model.__table__.columns:
            stmt = stmt.filter(self._model.is_deleted == False)

        # Statement without pagination
        stmt_without_pagination = stmt

        # Apply sorting if provided
        stmt = self.apply_sorting(stmt, sort_by)

        # Add pagination
        stmt = stmt.offset(offset).limit(limit)

        db_rows = await db.exec(stmt)
        data = [dict(row._mapping) for row in db_rows]

        # Get the total count of records matching the query
        total_count: int = await self.total_count(
            db=db, stmt_without_pagination=stmt_without_pagination
        )

        return {"data": data, "total_count": total_count}

    async def update(
        self,
        db: AsyncSession,
        object: Union[UpdateSchemaType, Dict[str, Any]],
        with_commit: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Update an existing record in the database.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        object : Union[UpdateSchemaType, Dict[str, Any]]
            The SQLModel (Pydantic) schema or dictionary containing the data to be updated.
        with_commit : bool, optional
            Flag indicating whether to commit the changes to the database.
        kwargs : dict
            Filters for the update.

        Returns
        -------
        None
        """
        # Extract the current user from the db session if it exists
        current_user = getattr(db, "current_user", {})

        if isinstance(object, dict):
            update_data = object
        else:
            update_data = object.model_dump(exclude_unset=True)

        # TODO: Verify if this is needed, because we use 'sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}' on TimestampMixin
        if "updated_at" in self._model.__table__.columns and "updated_at" in update_data.keys():
            update_data["updated_at"] = datetime.now(UTC)

        # Use correct user id for 'updated_by_user_id' if it exists
        if "updated_by_user_id" in self._model.__table__.columns:
            if "updated_by_user_id" in update_data.keys():
                update_data["updated_by_user_id"] = update_data["updated_by_user_id"]
            elif "id" in current_user.keys():
                update_data["updated_by_user_id"] = current_user["id"]
            else:
                update_data["updated_by_user_id"] = settings.USER_SYSTEM_ID

        # Update the record
        stmt = update(self._model).filter_by(**kwargs).values(update_data)

        await db.exec(stmt)

        # Commit or flush the changes
        if not with_commit:
            await db.flush()
        else:
            await db.commit()

    async def db_delete(self, db: AsyncSession, with_commit: bool = True, **kwargs: Any) -> None:
        """
        Delete a record in the database.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        with_commit : bool, optional
            Flag indicating whether to commit the changes to the database.
        kwargs : dict
            Filters for the delete.

        Returns
        -------
        None
        """
        stmt = delete(self._model).filter_by(**kwargs)

        await db.exec(stmt)

        # Commit or flush the changes
        if not with_commit:
            await db.flush()
        else:
            await db.commit()

    async def delete(self, db: AsyncSession, db_row: Row | None = None, **kwargs: Any) -> None:
        """
        Soft delete a record if it has "is_deleted" attribute, otherwise perform a hard delete.

        Parameters
        ----------
        db : AsyncSession
            The SQLModel async session.
        db_row : Row | None, optional
            Existing database row to delete. If None, it will be fetched based on `kwargs`. Default is None.
        kwargs : dict
            Filters for fetching the database row if not provided.

        Returns
        -------
        None
        """
        # Extract the current user
        current_user = getattr(db, "current_user", {})

        db_row = db_row or await self.exists(db=db, **kwargs)
        if db_row:
            if "is_deleted" in self._model.__table__.columns:
                # Soft delete
                object_dict = {
                    "is_deleted": True,
                    "deleted_at": datetime.now(UTC),
                }

                # Use correct user id for 'updated_by_user_id'
                if "updated_by_user_id" in self._model.__table__.columns:
                    if "id" in current_user.keys():
                        object_dict["updated_by_user_id"] = current_user["id"]
                    else:
                        object_dict["updated_by_user_id"] = settings.USER_SYSTEM_ID

                # Update the record
                stmt = update(self._model).filter_by(**kwargs).values(object_dict)

                await db.exec(stmt)
                await db.commit()

            else:
                stmt = delete(self._model).filter_by(**kwargs)
                await db.exec(stmt)
                await db.commit()
