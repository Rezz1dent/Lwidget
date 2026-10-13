plugins {
    id("com.android.application")
}

android {
    namespace = "com.leanbitlab.breezybridge"
    compileSdk = 36

    defaultConfig {
        // Independent package: can coexist with the original Lwidget.
        applicationId = "com.rezz1dent.breezykwgtbridge"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.2.0-provider-preview"
    }

    buildTypes {
        debug { versionNameSuffix = "-debug" }
        release { isMinifyEnabled = false }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
