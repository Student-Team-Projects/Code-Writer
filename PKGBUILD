pkgname=code-writer
pkgver=0.1.0
pkgrel=1
pkgdesc="AI-powered code solver — Code Writer"
arch=(x86_64)
url="https://example.local/"
license=('custom')
depends=('python')
makedepends=('python-pip' 'python-virtualenv')
source=("src" "config")

build() {
	return 0
}

package() {
	# Create package layout: place package root contents from `src/` at /opt/code-writer
	mkdir -p "$pkgdir/opt/$pkgname"
	# Copy Python application files from src/ so main.py ends up at /opt/code-writer/main.py
	if [ -d "$srcdir/src" ]; then
		mkdir -p "$pkgdir/opt/$pkgname"
		cp -a "$srcdir/src/." "$pkgdir/opt/$pkgname/"
	fi
	# Also copy config directory if present at project root
	if [ -d "$srcdir/config" ]; then
		cp -a "$srcdir/config" "$pkgdir/opt/$pkgname/"
	fi

	# Create a virtual environment inside the package and install Python deps there.
	if command -v python >/dev/null 2>&1; then
		python -m venv "$pkgdir/opt/$pkgname/venv"
		# Use the venv pip to install dependencies into the venv
		"$pkgdir/opt/$pkgname/venv/bin/python" -m pip install --upgrade pip setuptools || true
		"$pkgdir/opt/$pkgname/venv/bin/pip" install --no-deps --upgrade \
			'requests>=2.32' 'rich>=13.5.0' 'google-genai>=0.1.0' || echo "pip install into venv failed"
	else
		echo "Warning: python not available — venv and dependencies not installed."
	fi

	# Wrapper
	mkdir -p "$pkgdir/usr/bin"
	cat > "$pkgdir/usr/bin/code-writer" <<'EOF'
#!/bin/sh
cd /opt/code-writer || exit 1
exec /opt/code-writer/venv/bin/python /opt/code-writer/main.py "$@"
EOF
	chmod 755 "$pkgdir/usr/bin/code-writer"
}
