pkgname=code-writer
pkgver=0.1.0
pkgrel=1
pkgdesc="AI-powered code solver — Code Writer"
arch=(x86_64)
url="https://example.local/"
license=('custom')
depends=('python')
makedepends=('python-pip')
source=()

build() {
	return 0
}

package() {
	# Create package layout
	mkdir -p "$pkgdir/opt/$pkgname"
	cp -a "$srcdir/"* "$pkgdir/opt/$pkgname/"

	# Install Python packages into the package root via pip (preferred fallback).
	if command -v python >/dev/null 2>&1 && python -m pip --version >/dev/null 2>&1; then
		python -m pip install --root "$pkgdir" --upgrade --no-cache-dir \
			'requests>=2.32' 'rich>=13.5.0' 'google-genai>=0.1.0'
	else
		echo "Warning: pip not available — Python dependencies were not installed into package."
	fi

	# Wrapper
	mkdir -p "$pkgdir/usr/bin"
	cat > "$pkgdir/usr/bin/code-writer" <<'EOF'
#!/bin/sh
exec python3 /opt/code-writer/src/main.py "$@"
EOF
	chmod 755 "$pkgdir/usr/bin/code-writer"
}
