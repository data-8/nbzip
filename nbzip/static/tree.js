define([
    'jquery',
    'base/js/utils',
    'base/js/namespace'
], function (
    $, utils, Jupyter
) {

    var load_ipython_extension = function () {
        $(".col-sm-8.no-padding").attr('class', 'col-sm-4 no-padding');
        $(".col-sm-4.no-padding.tree-buttons").attr('class', 'col-sm-8 no-padding tree-buttons');

        $('#notebook_toolbar .pull-right').prepend(
          $('<div>').addClass('btn-group').attr('id', 'nbzip-link').prepend(
               '<button class="btn btn-xs btn-default" title="Zip Notebook"><i class="fa-download fa"></i></button>'
          ).click(function() {
             window.location.href = utils.get_body_data('baseUrl') + 'zip-download'
          })
        )
    };

    return {
        load_ipython_extension: load_ipython_extension,
    };

  });