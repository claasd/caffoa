from openapi_func_get.schema import generate_schemas
if __name__ == "__main__":
    generate_schemas("D:/data/btc/buntspecht/UserManagement/apis/service-api/userservice.openapi.yml",
                     "D:/data/btc/buntspecht/UserManagement/UserManagement/UserManagementFunction/Model",
                     "UserManagementFunction.Model")
