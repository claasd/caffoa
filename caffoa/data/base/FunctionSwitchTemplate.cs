var jObject = await ParseJson<JObject>(request.Body);
                var discriminator = jObject["{DISC}"]?.ToString();
                {VALUE} discriminator switch
                {{{{
                    {CASES},
                    _ => throw {JSON_ERROR_CLASS}.WrongContent("{DISC}", discriminator, new [] {{{{ {CASES_ALLOWED_VALUES} }}}})
                }}}};
