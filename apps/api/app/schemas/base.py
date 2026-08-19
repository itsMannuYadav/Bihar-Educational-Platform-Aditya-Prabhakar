from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelReadModel(BaseModel):
    """Response schemas backed by an ORM object via `model_validate(orm_obj)`.

    Validation stays keyed on the plain snake_case field name — so reading
    from a SQLAlchemy model needs no changes — while only the *serialization*
    alias is camelCased, matching what the TypeScript client expects on the
    wire (see packages/shared-types).
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=AliasGenerator(serialization_alias=to_camel),
    )


class CamelRequestModel(BaseModel):
    """Request bodies from the frontend: camelCase JSON in, snake_case
    Python fields. `populate_by_name` also allows constructing these
    directly with snake_case kwargs, e.g. in tests."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
