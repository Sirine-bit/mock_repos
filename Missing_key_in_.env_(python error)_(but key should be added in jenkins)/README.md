# Missing_key_in_.env_(python error)_(but key should be added in jenkins)

Redmine ingestion fixture for a Jenkins credential propagation problem.

The Python module requires `KAP_API_KEY`, but the Jenkins pipeline binds other
credentials and never exports that variable into the runtime environment.
