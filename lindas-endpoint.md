``` bash
curl -u "USERNAME:PASSWORD" \
  -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @test-upload.ttl \
  "https://int.graphdb.lindas.admin.ch/repositories/lindas/rdf-graphs/service?graph=https://lindas.admin.ch/fsvo/govtech26-tierseuchen-screener"
```

github-secrets:
- LINDAS_USERNAME
- LINDAS_PW

https://cognizone.atlassian.net/wiki/spaces/LEKB1/pages/150929410/Authentication+for+Write+Endpoints

https://lindas.admin.ch/fsvo/fsvo-govtech26-tierseuchen-screener