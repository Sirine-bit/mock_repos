# Root Cause Analysis: Could Not Auth - Git Authentication Failure

## Issue Summary
Jenkins pipeline `github_tcs_ingestion` fails during git checkout phase due to authentication failure with GitLab repository. The credentials provided through Jenkins credentials store are either invalid, expired, or incorrectly configured.

## Root Cause
Git authentication fails when attempting to clone/fetch from GitLab repository using the credential `token_gitlab_company_qqtechdataactivities`. This could be due to:

1. **Expired Token**: GitLab access token may have expired
2. **Invalid Credentials**: Token may be revoked or deleted from GitLab
3. **Insufficient Permissions**: Token may lack required scopes (api, read_repository, etc.)
4. **Credential Mapping Issue**: Jenkins credential ID doesn't match actual credential in store
5. **Network/Firewall**: GitLab server unreachable from Jenkins agent
6. **URL Mismatch**: Repository URL may have changed

## Technical Analysis

### Git Authentication Flow
1. Jenkins retrieves credential `token_gitlab_company_qqtechdataactivities` from credential store
2. Passes credential via GIT_ASKPASS environment variable
3. Git attempts to authenticate with GitLab using provided token
4. GitLab rejects authentication (HTTP 401/403)
5. Checkout operation fails

### Problematic Configuration
```groovy
checkout(
    scm: [
        $class: 'GitSCM',
        userRemoteConfigs: [[
            url: 'https://git.company-engineering.net/data/data-flow-hub',
            credentialsId: 'token_gitlab_company_qqtechdataactivities'
        ]]
    ]
)
```

### withCredentials Block
```groovy
withCredentials([
    string(credentialsId: 'GITHUB_SWBK_CREDENTIALS', variable: 'GITHUB_SWBK_TOKEN'),
    string(credentialsId: 'GITLAB_CARIAD_CREDENTIALS', variable: 'GITLAB_CARIAD_TOKEN'),
    string(credentialsId: 'CC_GITHUB_IPNEXT_CREDENTIALS', variable: 'GITHUB_IPNEXT_TOKEN'),
    string(credentialsId: 'MSSQL', variable: 'MSSQL_CREDS'),
    string(credentialsId: 'GITLAB_CREDENTIALS', variable: 'GITLAB_TOKEN')
])
```

**Note**: `token_gitlab_company_qqtechdataactivities` is used for checkout but is NOT defined in the withCredentials block - this may be a separate credential scope issue.

## Impact
- Complete pipeline failure at checkout stage
- No code retrieval possible
- Subsequent build steps blocked
- Development/deployment pipeline halted
- Cannot proceed with ingestion of test cases

## Diagnostics

### Step 1: Verify Credential Existence
```bash
# On Jenkins master, check if credential exists
curl -u admin:admin "http://jenkins.internal:8080/credentials/store/system/domain/_/" -k
```

### Step 2: Check Credential Details
- Log into Jenkins UI
- Navigate to: Manage Jenkins → Credentials
- Verify credential `token_gitlab_company_qqtechdataactivities` exists
- Check if credential is set to "Kind: Secret text" or "Username with password"

### Step 3: Test GitLab Access
```bash
# From Jenkins agent/master
curl -H "PRIVATE-TOKEN: <token>" "https://git.company-engineering.net/api/v4/projects" -v
```

### Step 4: Check Token Validity
```bash
# On GitLab web interface
# Go to Settings → Access Tokens
# Verify token: 
#   - Not expired
#   - Has correct scopes (api, read_repository, write_repository)
#   - Not revoked
```

### Step 5: Network Connectivity
```bash
# From Jenkins agent
ping git.company-engineering.net
curl -v "https://git.company-engineering.net/data/data-flow-hub.git" -H "Authorization: Bearer <token>"
```

## Remediation Steps

### Immediate Fix (Option 1 - Update Token)
1. Generate new GitLab personal access token:
   - Log into GitLab as user
   - Settings → Access Tokens
   - Create new token with scopes: `api`, `read_repository`, `write_repository`
   - Copy token

2. Update Jenkins credential:
   - Manage Jenkins → Credentials
   - Find `token_gitlab_company_qqtechdataactivities`
   - Click "Update"
   - Paste new token
   - Save

3. Re-run Jenkins job

### Immediate Fix (Option 2 - Use SSH)
Instead of HTTPS with token auth:
```groovy
checkout(
    scm: [
        $class: 'GitSCM',
        userRemoteConfigs: [[
            url: 'git@git.company-engineering.net:data/data-flow-hub.git',
            credentialsId: 'jenkins-ssh-key'
        ]]
    ]
)
```

### Verification Steps
1. Test credential manually:
   ```bash
   git clone https://<token>@git.company-engineering.net/data/data-flow-hub
   ```

2. Run Jenkins build with verbose logging:
   ```groovy
   withEnv(['GIT_TRACE=1', 'GIT_TRACE_PERFORMANCE=1']) {
       // checkout code
   }
   ```

3. Check Jenkins logs:
   - Jenkins console output for credential masking issues
   - Jenkins agent logs for authentication errors

## Prevention

### 1. Token Expiration Management
```groovy
// Add credential check stage
stage('Verify Credentials') {
    steps {
        script {
            withCredentials([string(credentialsId: 'token_gitlab_company_qqtechdataactivities', variable: 'GIT_TOKEN')]) {
                sh '''
                    curl -H "PRIVATE-TOKEN: $GIT_TOKEN" \
                         "https://git.company-engineering.net/api/v4/user" \
                         -f || exit 1
                '''
            }
        }
    }
}
```

### 2. Credential Audit Trail
- Set GitLab token expiration to 1 year
- Use GitLab audit logs to track token usage
- Implement automated token rotation (e.g., every 6 months)

### 3. Multiple Credential Fallbacks
```groovy
def gitClone(String url, String credId) {
    try {
        checkout([ ... credentialsId: credId ...])
    } catch (Exception e) {
        echo "Failed with credential: ${credId}, trying fallback..."
        checkout([ ... credentialsId: 'gitlab_backup_token' ...])
    }
}
```

### 4. Monitoring & Alerting
- Monitor Jenkins build failures for auth errors
- Alert on repeated 401/403 errors
- Track token expiration dates

## Related Issues
- Check all other jobs using `token_gitlab_company_qqtechdataactivities`
- Verify other credential configurations: GITHUB_*, GITLAB_*, MSSQL
- Review credential scope limitations

## Long-term Solution
Implement Jenkins-GitLab OAuth integration for automatic token management:
- GitLab plugin with OAuth
- Automatic token refresh
- Reduced manual credential management
- Better audit trail

## Testing
After remediation:
1. Run build in dry-run mode
2. Verify checkout completes successfully
3. Monitor for any authentication errors in logs
4. Test with different branches
5. Verify all credentials work correctly
