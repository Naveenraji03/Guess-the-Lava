# Guess the Lava Android APK project

This Android WebView app opens the Flask game server.

## Current server address

`http://10.153.6.246:5000`

The phone and computer must be on the same Wi-Fi network. Keep `app.py` running.

## Build with Android Studio

1. Install Android Studio and its Android SDK.
2. Open this `guess_the_lava_android` folder.
3. Wait for Gradle to finish syncing.
4. Select `Build > Build Bundle(s) / APK(s) > Build APK(s)`.
5. Copy the generated APK from `app/build/outputs/apk/` to an Android phone.

## Build with Gradle command line

Java 17 and the Android SDK must be configured first:

```powershell
gradlew assembleDebug
```

The debug APK will be created in `app/build/outputs/apk/debug/app-debug.apk`.

## Change server address

Edit `GAME_URL` in:

`app/src/main/java/com/guessthelava/game/MainActivity.java`
