import flask
import werkzeug
import flask_login

print(f"Flask: {flask.__version__}")
print(f"Werkzeug: {werkzeug.__version__}")
print(f"Flask-Login: {flask_login.__version__}")

# Try the problematic import
try:
    from werkzeug.urls import url_decode
    print("✓ url_decode import SUCCESSFUL")
except ImportError:
    try:
        from werkzeug.urls import url_decode
        print("✓ url_decode import SUCCESSFUL (alternative)")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("Try: pip install Werkzeug==2.3.7")