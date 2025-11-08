# Using Pydantic Models

Generated MCP tool wrappers use Pydantic for type safety and validation.

## Basic Usage

```python
from runtime.servers.git import git_status, GitStatusParams

# Create typed parameters
params = GitStatusParams(repo_path=".")

# Call tool (type-safe)
result = await git_status(params)
```

## Validation

Pydantic validates all inputs:

```python
# ✅ Valid
params = GitStatusParams(repo_path=".")

# ❌ Invalid (missing required field)
params = GitStatusParams()  # ValidationError

# ❌ Invalid (wrong type)
params = GitStatusParams(repo_path=123)  # ValidationError
```

## Optional Fields

```python
class SearchParams(BaseModel):
    query: str  # Required
    limit: Optional[int] = None  # Optional with default

# Both valid
params1 = SearchParams(query="test")
params2 = SearchParams(query="test", limit=10)
```

## Serialization

```python
# To dict
params = GitStatusParams(repo_path=".")
params_dict = params.model_dump()
# {"repo_path": "."}

# From dict
params = GitStatusParams.model_validate({"repo_path": "."})

# To JSON
json_str = params.model_dump_json()

# From JSON
params = GitStatusParams.model_validate_json('{"repo_path": "."}')
```

## Nested Models

```python
class Address(BaseModel):
    street: str
    city: str

class Person(BaseModel):
    name: str
    address: Address

# Usage
person = Person(
    name="John",
    address=Address(street="123 Main", city="NYC")
)
```

## Field Aliases

```python
class Config(BaseModel):
    repo_path: str = Field(alias="repoPath")

    class Config:
        populate_by_name = True  # Accept both snake_case and camelCase

# Both work
config1 = Config(repo_path=".")
config2 = Config(repoPath=".")
```

## Validation Errors

```python
from pydantic import ValidationError

try:
    params = GitStatusParams(invalid_field="value")
except ValidationError as e:
    print(e.errors())
    # [{'loc': ('repo_path',), 'msg': 'field required', 'type': 'value_error.missing'}]
```

## Custom Validators

```python
from pydantic import BaseModel, field_validator

class SearchParams(BaseModel):
    query: str
    limit: int = 10

    @field_validator('limit')
    @classmethod
    def limit_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('limit must be positive')
        return v
```
