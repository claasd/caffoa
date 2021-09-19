# caffoa: Create Azure Function From Open Api

[![PyPI - License](https://img.shields.io/pypi/l/caffoa)](https://pypi.org/project/caffoa/)
[![PyPI](https://img.shields.io/pypi/v/caffoa)](https://pypi.org/project/caffoa/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/caffoa)

Tool to autogenerate azure function templates for .NET from openapi declaration.
Instead of generating stubs, the goal is to be able to change the api and re-generate the files without overwriting your code.

Currently considered alpha state. If something does not work that you feel should work, create a ticket with your openapi spec.

It uses [prance](https://pypi.org/project/prance/) for parsing the openapi spec.

# Usage

As code generation needs a lot of configuration, all configuration is done using a config file in yaml format.

The minimal config file is as follows:
```yaml
config:
  version: 2
services:
  - apiPath: my-service.openapi.yml
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
python3 -m caffoa --config path_to_config.yml
```

## Create Azure Function template:

If you specified the `function` part in the config file, 
the tool will create two files in the specified target folder:
* MyClassNameFunction.generated.cs
* IMyClassNameService.generated.cs

Your job now is to create an implementation for the `IMyClassNameService` interface.

Furthermore, you need [Dependency Injection](https://docs.microsoft.com/en-us/azure/azure-functions/functions-dotnet-dependency-injection) to pass your implementation to the constructor of the function.

Now implement all the logic in your implementation of the interface. You can now change your API, and regenerate the generated files without overwriting your code.

## Create data objects from schemas

If you specified the `model` part in the config file, the tool will generate a file for each schema defined in the components section of the openapi definition. The filename will be the schema name converted to UpperCamelCase with generated.cs added to the end (Example: `user`will create a class `User` defined in the file `User.generated.cs`).
The file will contain a shared class, with all properties of the schema. You can implement a shared class in a different file to add logic to these objects.

### Restrictions 
* The schema must be defined in the components section.
* Furthermore, schemas may not be nested without reference.
(You can easily overcome this restriction by defining more schemas in the components section and have them reference each other.)
* allOf is implemented as inheritance, and therefore can only handle allOf with one reference and one direct configuration

## Advanced configuration options
There are multiple optional configuration options that you can use:
```yaml
config:
  version: 2 # 1 (legacy, default), 2 (current), 3 (experimental) 
  useFactory: false # version 2+ if set to true, a factory interface is created additionally to the Service interface. Useful if you need to have different behaviors based on headers.
  prefix: "Pre" # A prefix that is added to all model classes
  suffix: "Suf" # A suffix that is added to all model classes
  errorFolder: ./output/errors # version 3+ only. Folder where ClientError Exceptions are generated
  errorNamespace: MyErrorNamespace # # version 3+ only. Namespace for  ClientError Exceptions are generated
  imports: # a list of imports that will be added to most generated classes
    - MySpecialNamespace
  
services:
  - apiPath: userservice.openapi.yml
    config:
      prefix:  # overrides the config element from the global config
      suffix:  # overrides the config element from the global config
      useFactory:  # overrides the config element from the global config
      errorFolder:  # overrides the config element from the global config
      errorNamespace:  # overrides the config element from the global config
      imports: # overrides the imports from the global config
    function:
      name: MyClassName
      namespace: MyNamespace
      targetFolder: ./output
      functionsName: MyFunctions # name of the functions class. defaults to {name}Functions 
      interfaceName: IMyInterface # name of the interface class. defaults to I{name}Service. 
      interfaceNamespace: MyInterfaceNamespace # defaults to 'namespace'. If given, the interface uses this namespace
      interfaceTargetFolder: ./output/shared # defaults to 'targetFolder'. If given, the interface is written to this folder

      ## for version 1 and 2, you can add boilerplate code to each invocation. 
      ## you can add placeholders: {BASE} for the full invocation code, or {CALL} for just the function call.
      ## {BASE} will be replaced with "return await Service(req, log).{CALL};"
      ## {CALL} will be replaced with 'FunctionName(params)'
      boilerplate: |
        try {
            {BASE}
        catch(SomethingNotFoundException e) {
          return new HttpResponseMessage(HttpStatusCode.NotFound)
          {
              Content = new StringContent(err.Message)
          };
        }

      ## if you need specific imports for your boilerplate, add them here:
      imports: # overrides the imports from the config section
        - MyNamespace.Exceptions.SomethingNotFoundException
    model:
      namespace: MyNamespace.Model
      targetFolder: ./output/Model
      # you can exclude objects from generation:
      excludes:
       - objectToExclude
      # you can also generate only some classes
      include:
        - objectToInclude
        - otherObjectToInclude
      imports: # overrides the imports from the global config
        - someImport
      prefix: # (Deprecated for version 3+) override prefix from the config section
      suffix: # (Deprecated for version 3+) override suffix from the config section
```

## Version 3
If you have a well specified openapi doc, use only json request bodies and returns, and you want strict rules what you get to work with and what you return, you can try out version 3.

Version 3 parses the return and requestBody specifications, and handles the object wrapping for you. 
* Request bodies that have well-defined schemas will be deserialized to the object
* Responses that have well-defined schemas will be serialized to Json responses
* The interface will not have IActionResult returns, but need to return the actual object for the method
* The interface will have the actual type that was passed along in the body as parameter
* Errors (400-499) will be implemented as Exceptions, that you can throw in your implementation.
* If you return a JSON Object with your Errors, a derived class will be created for that
* If you have different return codes for one object (e.g. 200 or 201 for a put request), the return of the interface will be (YourObject, int).

Version 3 takes over a lot of boilerplate code for you. Furthermore, it forces you to not cut corners, as you cannot return a different object than the specification calls for.