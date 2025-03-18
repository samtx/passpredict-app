from datetime import datetime, date
from uuid import uuid4, UUID

from sqlalchemy import (
    Integer,
    String,
    Text,
    Date,
    Float,
    ForeignKey,
    DateTime,
    Uuid,
)
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship,
)
from sqlalchemy.schema import ExecutableDDLElement
from sqlalchemy.event import listens_for
from sqlalchemy.ext.compiler import compiles


class CreateFTS5Table(ExecutableDDLElement):

    def __init__(
        self,
        table,
        columns,
    ):
        self.table = table
        self.columns = columns


@compiles(CreateFTS5Table)
def create_fts5_table(element: CreateFTS5Table, compiler, **kwargs):
    sql_compiler = compiler.sql_compiler
    table_name = element.table.__tablename__
    fts_table_name = f"{table_name}_fts"
    columns = ", ".join((col for col in element.columns))
    row_id = sql_compiler.render_literal_value(element.table.primary_key, String())
    stmt = (
        f"CREATE VIRTUAL TABLE {fts_table_name} IF NOT EXISTS USING fts5("
        f"{columns}, content={table_name}, content_rowid={row_id});"
    )
    return stmt
