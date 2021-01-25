# coffoa: Create Azure Function From Open Api

[![PyPI - License](https://img.shields.io/pypi/l/caffoa)](https://pypi.org/project/caffoa/)
[![PyPI](https://img.shields.io/pypi/v/caffoa)](https://pypi.org/project/caffoa/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/caffoa)

Tool to autogenerate azure function templates for .NET from openapi declaration.
Instead of generating stubs, the goal is to be able to change the api and re-generate the files without overwriting your code.

Currently considered alpha state. If something does not work that you feel should work, create a ticket with your openapi spec.

It uses [prance](https://pypi.org/project/prance/) for parsing the openapi spec.

# Usage

you need a small config file in yaml format:
```yaml
services:
  - apiPath: userservice.openapi.yml
    function:
      name: MyClassName
      namespace: MyNamespace
      targetFolder: ./output
    model:
      namespace: MyNamespace.Model
      targetFolder: ./output/Model
```
You can add multiple services. Also, you can omit either `model` or `function` if you do not need one of them.
Then, call the tool: 

```bash
python3 -m caffoa --input path_to_config.yml
```

## Create Azure Function template:

If you specified the `function` part in the config file, 
the tool will create two files in the specified target folder:
* MyClassNameFunction.generated.cs
* IMyClassNameService.generated.cs

Your job now is to create an implementation for the `IMyClassNameService` interface.
Furthermore, the `MyClassNameFunction` is created as shared static class, with a shared static method called `private IMyClassNameService Service(HttpRequestMessage req, ILogger log);`
You need to implement this function in a different file (I suggest `MyClassNameFunction.cs`), that returns your implementation of the interface. You need tu use C# 9 to use this.

Now implement all the logic in your implementation of the interface. You can now change your API, and regenerate the generated files without overwriting your code.

## Create data objects from schemas

If you specified the `model` part in the config file, the tool will generate a file for each schema defined in the components section of the openapi definition. The filename will be the schema name converted to UpperCamelCase with generated.cs added to the end (Example: `user`will create a class `User` defined in the file `User.generated.cs`).
The file will contain a shared class, with all properties of the schema. You can implement a shared class in a different file to add logic to these objects.

### Restrictions 
* The schema must be defined in the components section.
* Furthermore, schemas may not be nested without reference.
(You can easily overcome this restriction by defining more schemas in the components section and have them reference each other.)
* allOf is implemented as inheritance
