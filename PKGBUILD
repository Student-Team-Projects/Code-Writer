pkgname=code-writer
pkgver=0.1.0
pkgrel=1
pkgdesc="AI-powered code solver — Code Writer"
arch=(x86_64)
url="https://example.local/"
license=('custom')
depends=('python' 'python-requests' 'python-rich')
makedepends=('python-pip')
source=()

build() {
	return 0
}

package() {
	# Create package layout
	mkdir -p "$pkgdir/opt/$pkgname"
	cp -a "$srcdir/"* "$pkgdir/opt/$pkgname/"

	# Attempt to install optional `python-google-genai` via pacman into the package root;
	# if it's not available in the repos, fall back to pip (makedepends includes python-pip).
	if pacman -Si python-google-genai >/dev/null 2>&1; then
		echo "Installing python-google-genai from repos into package root..."
		pacman -Sy --noconfirm --root "$pkgdir" --cachedir "$srcdir/.cache" python-google-genai || echo "pacman install failed"
	else
		echo "python-google-genai not found in repos; falling back to pip (if available)"
		if command -v python >/dev/null 2>&1 && python -m pip --version >/dev/null 2>&1; then
			python -m pip install --root "$pkgdir" --no-deps 'google-genai>=0.1.0' || echo "pip install failed"
		else
			echo "Warning: pip not available — google-genai not installed in package."
		fi
	fi

	# Wrapper
	mkdir -p "$pkgdir/usr/bin"
	cat > "$pkgdir/usr/bin/code-writer" <<'EOF'
#!/bin/sh
exec python3 /opt/code-writer/src/main.py "$@"
EOF
	chmod 755 "$pkgdir/usr/bin/code-writer"
}
