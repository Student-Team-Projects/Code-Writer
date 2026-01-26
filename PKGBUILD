pkgname=code-writer
pkgver=0.1.0
pkgrel=1
pkgdesc="AI-powered code solver — Code Writer"
arch=(x86_64)
url="https://github.com/youruser/code-writer"
license=('MIT')
depends=('python')
makedepends=('python-pip' 'python-virtualenv')
# We leave source empty because we are building from the local directory
source=()

package() {
    # 1. Prepare directories
    install -dm755 "$pkgdir/opt/$pkgname/src"
    install -dm755 "$pkgdir/usr/bin"

    # 2. Copy the project files from your current directory ($startdir)
    # We copy 'src', 'resources', and any config folders
    # Using $startdir ensures we get files outside the (empty) srcdir
    cp -rp "$startdir/src"/* "$pkgdir/opt/$pkgname/src"
    
    # Copy config and resources if they exist
    [ -d "$startdir/config" ] && cp -rp "$startdir/config" "$pkgdir/opt/$pkgname/"
    [ -d "$startdir/resources" ] && cp -rp "$startdir/resources" "$pkgdir/opt/$pkgname/"
    [ -d "$startdir/CodeWriter" ] && cp -rp "$startdir/CodeWriter" "$pkgdir/opt/$pkgname/src"

    # 3. Set up the Virtual Environment inside the package
    # This keeps your system python clean!
    python -m venv "$pkgdir/opt/$pkgname/venv"
    
    # We must use the venv's python to install to the right path
    # We use --no-warn-script-location because we are in a "fake" root
    "$pkgdir/opt/$pkgname/venv/bin/python" -m pip install --upgrade pip
    "$pkgdir/opt/$pkgname/venv/bin/pip" install \
        'requests>=2.32' \
        'rich>=13.5.0' \
        'google-genai>=0.1.0' \
        'argparse' \
        'websockets'

    # 4. Create the Wrapper Script
    # This script will live in /usr/bin/code-writer
    cat > "$pkgdir/usr/bin/code-writer" <<EOF
#!/bin/sh
# Navigate to the app dir so relative paths for configs work
cd /opt/$pkgname
# Run using the isolated venv python
exec /opt/$pkgname/venv/bin/python /opt/$pkgname/src/main.py "\$@"
EOF

    chmod 755 "$pkgdir/usr/bin/code-writer"
    
    # 5. Fix permissions (Ensure the venv is usable by all users)
    find "$pkgdir/opt/$pkgname" -type d -exec chmod 755 {} +
    find "$pkgdir/opt/$pkgname" -type f -exec chmod 644 {} +
    chmod 755 "$pkgdir/opt/$pkgname/venv/bin/python"
    [ -f "$pkgdir/opt/$pkgname/src/main.py" ] && chmod 755 "$pkgdir/opt/$pkgname/src/main.py"
}
