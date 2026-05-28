import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  ActivityIndicator,
  BackHandler,
  Text,
  TouchableOpacity,
  Platform,
  SafeAreaView,
  Animated,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { WebView, WebViewNavigation } from 'react-native-webview';
import * as SplashScreen from 'expo-splash-screen';

SplashScreen.preventAutoHideAsync();

const APP_URL = 'https://bonyanplus.com';
const BRAND_COLOR = '#0e4d8d';
const BRAND_DARK = '#0a3a6e';

export default function App() {
  const webViewRef = useRef<WebView>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [canGoBack, setCanGoBack] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const loadingProgress = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    SplashScreen.hideAsync();
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 400,
      useNativeDriver: true,
    }).start();
  }, []);

  // Animate loading bar
  useEffect(() => {
    if (isLoading) {
      loadingProgress.setValue(0);
      Animated.timing(loadingProgress, {
        toValue: 0.8,
        duration: 3000,
        useNativeDriver: false,
      }).start();
    } else {
      Animated.timing(loadingProgress, {
        toValue: 1,
        duration: 200,
        useNativeDriver: false,
      }).start(() => loadingProgress.setValue(0));
    }
  }, [isLoading]);

  // Android back button
  useEffect(() => {
    if (Platform.OS !== 'android') return;
    const handler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (canGoBack && webViewRef.current) {
        webViewRef.current.goBack();
        return true;
      }
      return false;
    });
    return () => handler.remove();
  }, [canGoBack]);

  const handleNavigationStateChange = useCallback((navState: WebViewNavigation) => {
    setCanGoBack(navState.canGoBack);
  }, []);

  const handleReload = useCallback(() => {
    setHasError(false);
    setIsLoading(true);
    webViewRef.current?.reload();
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    webViewRef.current?.reload();
    setTimeout(() => setRefreshing(false), 1500);
  }, []);

  const progressWidth = loadingProgress.interpolate({
    inputRange: [0, 1],
    outputRange: ['0%', '100%'],
  });

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" backgroundColor={BRAND_DARK} />

      {/* Loading Bar */}
      {isLoading && !hasError && (
        <View style={styles.progressBar}>
          <Animated.View style={[styles.progressFill, { width: progressWidth }]} />
        </View>
      )}

      <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
        {hasError ? (
          <ScrollView
            contentContainerStyle={styles.errorContainer}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={handleRefresh}
                colors={[BRAND_COLOR]}
                tintColor={BRAND_COLOR}
              />
            }
          >
            <View style={styles.errorCard}>
              <Text style={styles.errorIcon}>🌐</Text>
              <Text style={styles.errorTitle}>تعذّر تحميل الصفحة</Text>
              <Text style={styles.errorSubtitle}>
                تأكد من اتصالك بالإنترنت ثم حاول مرة أخرى
              </Text>
              <TouchableOpacity
                style={styles.retryButton}
                onPress={handleReload}
                activeOpacity={0.85}
              >
                <Text style={styles.retryText}>↻  إعادة المحاولة</Text>
              </TouchableOpacity>
              <Text style={styles.pullHint}>أو اسحب للأسفل للتحديث</Text>
            </View>
          </ScrollView>
        ) : (
          <>
            <WebView
              ref={webViewRef}
              source={{ uri: APP_URL }}
              style={styles.webview}
              onLoadStart={() => setIsLoading(true)}
              onLoadEnd={() => setIsLoading(false)}
              onError={() => {
                setHasError(true);
                setIsLoading(false);
              }}
              onHttpError={(e) => {
                if (e.nativeEvent.statusCode >= 500) {
                  setHasError(true);
                  setIsLoading(false);
                }
              }}
              onNavigationStateChange={handleNavigationStateChange}
              javaScriptEnabled
              domStorageEnabled
              allowsBackForwardNavigationGestures
              pullToRefreshEnabled
              mediaPlaybackRequiresUserAction={false}
              allowsInlineMediaPlayback
              mixedContentMode="compatibility"
              allowsFullscreenVideo
              geolocationEnabled
              userAgent={
                Platform.OS === 'android'
                  ? 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 BonyanPlusApp/1.0'
                  : 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1 BonyanPlusApp/1.0'
              }
            />

            {/* Initial loading overlay */}
            {isLoading && (
              <View style={styles.loadingOverlay}>
                <View style={styles.loadingCard}>
                  <ActivityIndicator size="large" color={BRAND_COLOR} />
                  <Text style={styles.loadingText}>بنيان بلس</Text>
                  <Text style={styles.loadingSubText}>جاري التحميل...</Text>
                </View>
              </View>
            )}
          </>
        )}
      </Animated.View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: BRAND_DARK,
  },
  progressBar: {
    height: 3,
    backgroundColor: 'rgba(255,255,255,0.2)',
    width: '100%',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4fc3f7',
  },
  content: {
    flex: 1,
    backgroundColor: '#fff',
  },
  webview: {
    flex: 1,
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#f0f4f8',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingCard: {
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 22,
    fontWeight: 'bold',
    color: BRAND_COLOR,
    marginTop: 8,
  },
  loadingSubText: {
    fontSize: 14,
    color: '#888',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f4f8',
    padding: 24,
    minHeight: 500,
  },
  errorCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 36,
    alignItems: 'center',
    width: '100%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 5,
  },
  errorIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 10,
    textAlign: 'center',
  },
  errorSubtitle: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 28,
  },
  retryButton: {
    backgroundColor: BRAND_COLOR,
    paddingHorizontal: 36,
    paddingVertical: 14,
    borderRadius: 12,
    shadowColor: BRAND_COLOR,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 4,
    marginBottom: 16,
  },
  retryText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  pullHint: {
    fontSize: 12,
    color: '#bbb',
    marginTop: 4,
  },
});
