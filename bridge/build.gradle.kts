plugins {
    id("com.android.application")
}

android {
    namespace = "com.leanbitlab.breezybridge"
    compileSdk = 36

    defaultConfig {
        // Breezy sends Gadgetbridge updates explicitly to this installed package.
        // This is a lightweight replacement for Lwidget; the two cannot coexist.
        applicationId = "com.leanbitlab.lwidget"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1-bridge"
    }

    buildTypes {
        debug {
            versionNameSuffix = "-debug"
        }
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
