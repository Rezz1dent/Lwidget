plugins {
    id("com.android.application")
}

android {
    namespace = "com.leanbitlab.breezybridge"
    compileSdk = 36

    defaultConfig {
        // Independent app ID: uses Breezy ContentProvider, coexists with Lwidget.
        applicationId = "com.rezz1dent.breezykwgtbridge"
        minSdk = 26
        targetSdk = 36
        versionCode = 7
        versionName = "1.4"
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
