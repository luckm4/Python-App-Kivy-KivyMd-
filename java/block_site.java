package cecotein.informatica.cespreitaapp.informatica;

import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.util.ArrayList;

public class MyWebViewClient extends WebViewClient {
    private ArrayList<String> blockedUrls;

    public MyWebViewClient(ArrayList<String> blockedUrls) {
        this.blockedUrls = blockedUrls;
    }

    @Override
    public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
        String url = request.getUrl().toString();
        
        // Verifica se a URL é bloqueada
        for (String blockedUrl : blockedUrls) {
            if (url.contains(blockedUrl)) {
                // Se a URL estiver na lista de bloqueio, não carrega
                return true;
            }
        }
        
        // Se não estiver na lista de bloqueio, carrega normalmente
        return false;
    }
}
