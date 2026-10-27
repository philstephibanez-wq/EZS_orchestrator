(function($){
  if (!$) return;
  $(function(){
    const $status=$('#prod-control-status'),$mode=$('#prod-maintenance'),$edge=$('#prod-caddy'),$btn=$('#prod-maintenance-button');
    let token='',busy=false;
    function refreshProd(){
      $.ajax({url:'/api/v2/infrastructure/prod-control',dataType:'json',cache:false,timeout:5000})
       .done(function(d){
         if(d.schema!=='ezs.prod_control.v1') return;
         token=d.csrf||'';
         $mode.text(d.maintenance===true?'Activée':d.maintenance===false?'Mode normal':'Indéterminée');
         $edge.text(d.caddy_listening?'Écoute 8501':'Arrêté');
         $status.text(d.gateway_online?'Gateway active': 'Gateway absente');
         $btn.prop('disabled',busy||!d.actions.maintenance||d.maintenance===true);
       }).fail(function(){$status.text('État indisponible');$btn.prop('disabled',true);});
    }
    $btn.on('click',function(){
      if(busy||!token||!window.confirm('Activer la maintenance EZScore PROD ?')) return;
      busy=true;$btn.prop('disabled',true);
      $.ajax({url:'/api/v2/infrastructure/prod-control/maintenance',method:'POST',data:{confirmation:'MAINTENANCE'},headers:{'X-EZS-CSRF':token},timeout:15000})
       .done(function(){$status.text('Maintenance activée');})
       .fail(function(){$status.text('Échec de la commande — consulter les journaux');})
       .always(function(){busy=false;refreshProd();});
    });
    refreshProd();
    window.setInterval(function(){if(!document.hidden&&!busy)refreshProd();},15000);
    $('#refresh-dev-health').on('click',refreshProd);
  });
})(window.jQuery);
