(function($){
  if (!$) return;
  $(function(){
    const $status=$('#prod-control-status'),$mode=$('#prod-maintenance'),$edge=$('#prod-caddy');
    const $maintenance=$('#prod-maintenance-button'),$normal=$('#prod-normal-button');
    let token='',busy=false;
    function refreshProd(){
      $.ajax({url:'/api/v2/infrastructure/prod-control',dataType:'json',cache:false,timeout:5000})
       .done(function(d){
         if(d.schema!=='ezs.prod_control.v1') return;
         token=d.csrf||'';
         $mode.text(d.maintenance===true?'Activée':d.maintenance===false?'Mode normal':'Indéterminée');
         $edge.text(d.caddy_listening?'Écoute 8501':'Arrêté');
         $status.text(d.gateway_online?(d.backend_ready?'Gateway et Symfony actifs':'Gateway active, backend indisponible'):'Gateway absente');
         $maintenance.prop('disabled',busy||!d.actions.maintenance);
         $normal.prop('disabled',busy||!d.actions.normal);
         $normal.attr('title',d.note||'');
       }).fail(function(){
         $status.text('État indisponible');
         $maintenance.prop('disabled',true);$normal.prop('disabled',true);
       });
    }
    function command(action,confirmation,message){
      if(busy||!token||!window.confirm(message)) return;
      busy=true;$maintenance.prop('disabled',true);$normal.prop('disabled',true);
      $.ajax({
        url:'/api/v2/infrastructure/prod-control/'+action,
        method:'POST',data:{confirmation:confirmation},
        headers:{'X-EZS-CSRF':token},timeout:30000
      }).done(function(d){
        $status.text(d.result||'Commande exécutée');
      }).fail(function(xhr){
        const d=xhr.responseJSON||{};
        $status.text('Échec : '+(d.error||'commande refusée'));
      }).always(function(){busy=false;refreshProd();});
    }
    $maintenance.on('click',function(){command('maintenance','MAINTENANCE','Activer la maintenance EZScore PROD ?');});
    $normal.on('click',function(){command('normal','NORMAL','Désactiver la maintenance et exposer EZScore PROD sur Internet ? Vérifier ensuite Google SSO.');});
    refreshProd();
    window.setInterval(function(){if(!document.hidden&&!busy)refreshProd();},15000);
    $('#refresh-dev-health').on('click',refreshProd);
  });
})(window.jQuery);
