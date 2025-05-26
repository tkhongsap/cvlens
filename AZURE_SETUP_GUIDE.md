# Azure AD Setup Guide for CVLens-Agent

## Fixing "AADSTS500113: No reply address is registered" Error

### Problem
When trying to authenticate, you're getting the error:
```
AADSTS500113: No reply address is registered for the application.
```

### Solution

1. **Go to Azure Portal**
   - Navigate to: https://portal.azure.com
   - Sign in with your account: totrakool.k@thaibev.com

2. **Find Your App Registration**
   - Go to: Azure Active Directory → App registrations
   - Click on: CVLens - Agent

3. **Configure Authentication**
   - Click "Authentication" in the left menu
   - Click "Add a platform" button
   - Select "Mobile and desktop applications"

4. **Add Redirect URI**
   Add this exact URI:
   ```
   https://login.microsoftonline.com/common/oauth2/nativeclient
   ```

5. **Configure Public Client Settings**
   Scroll down to "Advanced settings" and ensure:
   - "Allow public client flows" is set to "Yes"

6. **Save Changes**
   - Click "Save" at the top

### Alternative URIs (if the above doesn't work)
You can also try adding these redirect URIs:
```
http://localhost
urn:ietf:wg:oauth:2.0:oob
```

### Verification
After making these changes:
1. Wait 1-2 minutes for changes to propagate
2. Run the test again:
   ```bash
   python test_azure_connection.py
   ```

### Your App Details
- **Application Name**: CVLens - Agent
- **Client ID**: 9a1e2246-8131-4893-a1ef-87280e20cf49
- **Tenant ID**: 1d8f5d85-9109-4cda-abcf-3fa469cbf8f9
- **Email**: totrakool.k@thaibev.com

### Important Notes
- The redirect URI must match exactly (including https://)
- Device code flow requires "public client" configuration
- Changes may take a few minutes to take effect

### If Still Having Issues
1. Check that your app is configured as a "Public client" (not confidential)
2. Ensure "Supported account types" includes your organization
3. Verify API permissions include "Mail.Read" and "offline_access" 