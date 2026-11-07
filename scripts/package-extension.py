"""Build the small, dependency-free local integration extension."""
from pathlib import Path
from zipfile import ZipFile
source=Path('/opt/study-extension')
with ZipFile('/tmp/study-bridge.vsix','w') as bundle:
    for name in ['package.json','extension.js']:
        bundle.write(source/name,'extension/'+name)
    bundle.writestr('[Content_Types].xml','''<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/><Default Extension="vsixmanifest" ContentType="text/xml"/></Types>''')
    bundle.writestr('extension.vsixmanifest','''<?xml version="1.0"?><PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011"><Metadata><Identity Language="en-US" Id="study-bridge" Version="1.0.0" Publisher="openssl-study"/><DisplayName>OpenSSL Study</DisplayName><Description xml:space="preserve">Local lesson integration</Description><Properties><Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.90.0"/></Properties></Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/><Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets></PackageManifest>''')
