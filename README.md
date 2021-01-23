# aoffoa: Create Azure Function From Open Api

[![PyPI - License](https://img.shields.io/pypi/l/caffoa)](https://pypi.org/project/caffoa/)
[![PyPI](https://img.shields.io/pypi/v/caffoa)](https://pypi.org/project/cafooa/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/caffoa)

Tool to autogenerate azure function templates for .NET from openapi declaration.
Instead of generating stubs, the goal is to be able to change the api and re-generate the files without overwriting your code.

Currently considered alpha state. If something does not work that you feel should work, create a ticket with your openapi spec.

It uses [prance](https://pypi.org/project/prance/) for parsing the openapi spec.

# Usage

## Create Azure Function template:
```bash
python3 -m caffoa functions --input path_to_openapi_yaml --output-folder path/to/output/ -- namespace Company.Function --class-name MyClassName
```
This will create two files in the output folder:
* MyClassNameFunction.generated.cs
* IMyClassService.generated.cs

Your job now is to create an implementation for the `IMyClassService` interface.
Furthermore, the `MyClassNameFunction` is created as shared static class, with a shared static method called `IMyClassService Service(HttpRequestMessage, ILogger log);`
You need to implement this function in a different file (I suggest `MyClassFunction.cs`), that returns your implementation of the interface. You need tu use C# 9 to use this.

Now implement all the logic in your implementation of the interface. You can now change your API, and regenerate the generated files without overwriting your code.

## Create data objects from schemas

* The schema must be defined in the components section.
* Furthermore, schemas may not be nested without reference.
(You can easily overcome this restriction by defining more schemas in the components section and have them reference each other.)
* allOf is implemented as inheritance.

```bash
python3 -m caffoa schemas --input path_to_openapi_yaml --output-folder path/to/output/models/ -- namespace Company.Function.Models
```

this will generate a file for each schema defined in the components section. The filename will be the schema name converted to UpperCamelCase with generated.cs added to the end.
The file will contain a shared class, with all properties of the schema. You can implement a shared class in a different file to add logic to these objects.
 