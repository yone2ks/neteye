from neteye import app
from neteye.extensions import settings

print(app.url_map)
app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
