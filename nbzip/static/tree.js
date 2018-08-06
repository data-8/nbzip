define([
    'jquery',
    'base/js/utils',
    'base/js/namespace'
], function (
    $, utils, Jupyter
) {

    // inspired by: https://stackoverflow.com/questions/1106377/detect-when-browser-receives-file-download
    var currToken = null;

    var newToken = function () {
      return new Date().getTime();
    }

    getCookie = function ( name ) {
      var parts = document.cookie.split(name + "=");
      if (parts.length == 2) return parts.pop().split(";").shift();
    }

    expireCookie = function ( cName ) {
        document.cookie =
            encodeURIComponent(cName) + "=deleted; expires=" + new Date( 0 ).toUTCString();
    }

    var load_ipython_extension = function () {
        $(".col-sm-8.no-padding").attr('class', 'col-sm-4 no-padding');
        $(".col-sm-4.no-padding.tree-buttons").attr('class', 'col-sm-8 no-padding tree-buttons');

        $('#notebook_toolbar .pull-right').prepend(
          $('<div>').addClass('btn-group').attr('id', 'nbzip-ziplink').prepend(
               '<button class="btn btn-xs btn-default" title="Download as ZIP"><i class="fa-download fa"></i></button>'
          ).click(function() {
            baseUrl = document.location.origin + document.body.getAttribute('data-base-url');
            zipPath = document.body.getAttribute('data-notebook-path');
            currToken = newToken();

            window.location.href = baseUrl + 'zip-download?zipPath=' + zipPath + '&zipToken=' + currToken + 'format=zip';
            $("#nbzip-ziplink").html("Zipping...");

            tid = setInterval(function() {
              if (getCookie("zipToken") == currToken) {
                console.log("Finished zipping & downloading notebook.");
                clearInterval(tid);
                expireCookie("zipToken");
                $("#nbzip-ziplink").html(
                  '<button class="btn btn-xs btn-default" title="Download as ZIP"><i class="fa-download fa"></i></button>'
                )
              } else {
                console.log("Still zipping...");
              }
            }, 1000);
          })
        )
    };

    return {
        load_ipython_extension: load_ipython_extension,
    };

  });
