import React, { useState, useRef, useEffect } from 'react';
import {
  StyleSheet, View, ActivityIndicator, BackHandler,
  Text, TouchableOpacity, Platform, SafeAreaView,
  StatusBar, Animated,
} from 'react-native';
import { WebView } from 'react-native-webview';

const APP_URL = 'https://bonyanplus.com';
const BRAND = '#0e4d8d';

export default function App() {
  const webRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [canBack, setCanBack] = useState(false);
  const fade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fade, { toValue: 1, duration: 500, useNativeDriver: true }).start();
  }, []);

  useEffect(() => {
    if (Platform.OS !== 'android') return;
    const h = BackHandler.addEventListener('hardwareBackPress', () => {
      if (canBack && webRef.current) { webRef.current.goBack(); return true; }
      return false;
    });
    return () => h.remove();
  }, [canBack]);

  return (
    <SafeAreaView style={s.root}>
      <StatusBar barStyle="light-content" backgroundColor={BRAND} />
      <Animated.View style={[s.box, { opacity: fade }]}>
        {error ? (
          <View style={s.err}>
            <Text style={s.errIcon}>🌐</Text>
            <Text style={s.errTitle}>لا يوجد اتصال بالإنترنت</Text>
            <Text style={s.errSub}>تحقق من الاتصال وحاول مرة أخرى</Text>
            <TouchableOpacity style={s.btn} onPress={() => { setError(false); setLoading(true); webRef.current?.reload(); }}>
              <Text style={s.btnTxt}>↻  إعادة المحاولة</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            <WebView
              ref={webRef}
              source={{ uri: APP_URL }}
              style={s.web}
              onLoadStart={() => setLoading(true)}
              onLoadEnd={() => setLoading(false)}
              onError={() => { setError(true); setLoading(false); }}
              onNavigationStateChange={n => setCanBack(n.canGoBack)}
              javaScriptEnabled
              domStorageEnabled
              pullToRefreshEnabled
              allowsBackForwardNavigationGestures
            />
            {loading && (
              <View style={s.loader}>
                <ActivityIndicator size="large" color={BRAND} />
                <Text style={s.loaderTxt}>بنيان بلس</Text>
                <Text style={s.loaderSub}>جاري التحميل...</Text>
              </View>
            )}
          </>
        )}
      </Animated.View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#0a3a6e' },
  box: { flex: 1, backgroundColor: '#fff' },
  web: { flex: 1 },
  loader: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#f0f4f8',
    justifyContent: 'center', alignItems: 'center', gap: 12,
  },
  loaderTxt: { fontSize: 22, fontWeight: 'bold', color: '#0e4d8d', marginTop: 8 },
  loaderSub: { fontSize: 14, color: '#888' },
  err: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32, backgroundColor: '#f0f4f8' },
  errIcon: { fontSize: 64, marginBottom: 16 },
  errTitle: { fontSize: 20, fontWeight: 'bold', color: '#111', marginBottom: 8, textAlign: 'center' },
  errSub: { fontSize: 14, color: '#888', textAlign: 'center', lineHeight: 22, marginBottom: 28 },
  btn: { backgroundColor: '#0e4d8d', paddingHorizontal: 36, paddingVertical: 14, borderRadius: 12 },
  btnTxt: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
