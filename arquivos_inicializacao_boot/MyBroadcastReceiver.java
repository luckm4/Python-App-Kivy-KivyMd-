// O MyBroadcastReceiver.java é responsavel por receber a requisição do AndroidManifest.tmpl.xml quando o dispositivo é reiniciado

package cecotein.informatica.cespreitaapp.informatica;

import android.content.BroadcastReceiver;
import android.content.Intent;
import android.content.Context;
import cecotein.informatica.cespreitaapp.informatica.ServiceMyservice;

public class MyBroadcastReceiver extends BroadcastReceiver {
    // Quando a requisição do xml for recebida ele executa este "void"
    public void onReceive(Context context, Intent intent) {
        // Estas linhas abaixo são responsaveis por iniciar o processo do CEspreita em segundo plano quando o dispositivo for reiniciado
        String package_root = context.getFilesDir().getAbsolutePath();
        String app_root =  package_root + "/app";

        Intent ix = new Intent(context, ServiceMyservice.class);

        ix.putExtra("androidPrivate", package_root);
        ix.putExtra("androidArgument", app_root);
        ix.putExtra("serviceEntrypoint", "./service.py");
        ix.putExtra("pythonName", "Myservice");
        ix.putExtra("serviceStartAsForeground", "true");
        ix.putExtra("pythonHome", app_root);
        ix.putExtra("pythonPath", package_root);
        ix.putExtra("pythonServiceArgument", app_root+":"+app_root+"/lib");
        ix.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);

        // Inicia o service.py com todos os parametros definidos e colocados dentro da váriavel "ix"
        context.startService(ix);
    }
}