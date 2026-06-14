"""Shared model utilities.

``PyObjectId`` lets Pydantic v2 validate and serialise MongoDB ``ObjectId``
values as strings, so domain models can round-trip cleanly to/from Mongo and
JSON without leaking BSON types into the API.
"""

from __future__ import annotations

from typing import Annotated, Any

from bson import ObjectId
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class _ObjectIdPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        def validate(value: Any) -> ObjectId:
            if isinstance(value, ObjectId):
                return value
            if isinstance(value, str) and ObjectId.is_valid(value):
                return ObjectId(value)
            raise ValueError("Invalid ObjectId")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.chain_schema(
                [core_schema.str_schema(), core_schema.no_info_plain_validator_function(validate)]
            ),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


PyObjectId = Annotated[ObjectId, _ObjectIdPydanticAnnotation]
