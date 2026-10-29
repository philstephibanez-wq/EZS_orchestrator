(function($){
  if (!$) return;
  $(function(){
    const $status=$('#prod-control-status'),$mode=$('#prod-maintenance'),$modeDetail=$('#prod-maintenance-detail'),$edge=$('#prod-caddy'),$edgeDetail=$('#prod-caddy-detail');
    const $maintenance=$('#prod-maintenance-button'),$normal=$('#prod-normal-button');
    const modalEl=document.getElementById('prod-action-modal');
    const modal=modalEl && window.bootstrap ? new window.bootstrap.Modal(modalEl) : null;
    const $title=$('#prod-action-modal-title'),$description=$('#prod-action-modal-description');
    const $error=$('#prod-action-modal-error'),$confirm=$('#prod-action-confirm');
    let token='',busy=false,pending=null,capabilities={maintenance:false,normal:false};
    function setButtons(){
      $maintenance.prop('disabled',busy||!capabilities.maintenance||!modal);
      $normal.prop('disabled',busy||!capabilities.normal||!modal);
    }
    function setStatus(label, level){
      $status.text(label).removeClass('text-bg-secondary text-bg-success text-bg-warning text-bg-danger')
        .addClass('text-bg-'+level);
    }
    function refreshProd(){
      $.ajax({url:'/api/v2/infrastructure/prod-control',dataType:'json',cache:false,timeout:5000})
       .done(function(d){
         if(d.schema!=='ezs.prod_control.v1') return;
         token=d.csrf||'';
         const maintenanceText=d.maintenance===true?'Activée':d.maintenance===false?'Mode normal':'Indéterminée';
         $mode.text(maintenanceText);
         $modeDetail.text(maintenanceText);
         $edge.text(d.caddy_listening?'Écoute 8501':'Arrêté');
         $edgeDetail.text(d.caddy_listening?'Écoute 8501':'Arrêté');
         if (d.gateway_online && d.backend_ready) {
           setStatus('Gateway et Symfony actifs','success');
         } else if (d.gateway_online) {
           setStatus('Gateway active, backend indisponible','warning');
         } else {
           setStatus('Gateway absente','danger');
         }
         capabilities={maintenance:!!d.actions.maintenance,normal:!!d.actions.normal};
         $normal.attr('title',d.note||'');
         setButtons();
       }).fail(function(){
         setStatus('État indisponible','secondary');
         $mode.text('Indéterminée');$modeDetail.text('Indéterminée');
         $edge.text('Indéterminé');$edgeDetail.text('Indéterminé');
         capabilities={maintenance:false,normal:false};setButtons();
       });
    }
    function ask(action){
      if(busy||!token||!modal||!capabilities[action]) return;
      pending=action;
      const normal=action==='normal';
      $title.text(normal?'Passer EZScore PROD en mode normal':'Activer la maintenance PROD');
      $description.text(normal?
        'Désactiver la maintenance et rendre EZScore PROD accessible sur Internet ? Vérifiez ensuite la connexion Google SSO.':
        'Activer la maintenance publique d’EZScore PROD ? Les utilisateurs ne pourront plus accéder à l’application.');
      $confirm.text(normal?'Activer le mode normal':'Activer la maintenance')
        .toggleClass('btn-success',normal).toggleClass('btn-warning',!normal);
      $error.prop('hidden',true).text('');
      modal.show();
    }
    function execute(){
      if(busy||!pending||!token||!capabilities[pending]) return;
      const action=pending;
      busy=true;setButtons();$confirm.prop('disabled',true);
      $.ajax({
        url:'/api/v2/infrastructure/prod-control/'+action,
        method:'POST',data:{confirmation:action==='normal'?'NORMAL':'MAINTENANCE'},
        headers:{'X-EZS-CSRF':token},timeout:30000
      }).done(function(d){
        setStatus(d.result||'Commande exécutée','secondary');
        modal.hide();
      }).fail(function(xhr){
        const d=xhr.responseJSON||{};
        $error.text('Commande refusée : '+(d.error||'échec technique')).prop('hidden',false);
      }).always(function(){
        busy=false;$confirm.prop('disabled',false);refreshProd();
      });
    }
    $maintenance.on('click',function(){ask('maintenance');});
    $normal.on('click',function(){ask('normal');});
    $confirm.on('click',execute);
    $(modalEl).on('hidden.bs.modal',function(){pending=null;$error.prop('hidden',true).text('');});
    refreshProd();
    window.setInterval(function(){if(!document.hidden&&!busy)refreshProd();},15000);
    $('#refresh-dev-health').on('click',refreshProd);
  });
})(window.jQuery);
