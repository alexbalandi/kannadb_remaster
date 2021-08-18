$(document).ready(function () {

  var filters = [
    ['weapon-type', 24],
    ['movement-type', 25],
    ['f2p', 26],
    ['book', 27],
    ['generation', 28],
    ['availability', 29],
    ['origin_game', 31],
    ['gender', 33],
    ['dancer', 34],
    ['resplendent', 37],
    ['season', 38],
  ];
  var column_visibility = {};
  column_visibility.normal = [4, 5, 6, 7, 8, 9];
  column_visibility.max = [10, 11, 12, 13, 14, 15];
  column_visibility.none = [4, 5, 6, 7, 8, 9];
  column_visibility.adjusted = [16, 17, 18, 19, 20, 21];
  var current_vis = 'normal';

  $(".stat-range-slider-widget").each(function (index) {
    var datamin = parseFloat($(this).attr("data-min"));
    var datamax = parseFloat($(this).attr("data-max"));
    var datafor = $(this).attr("data-for");
    $(this).slider({
      range: true,
      min: datamin,
      max: datamax,
      values: [datamin, datamax],
      slide: function (event, ui) {
        $('#' + datafor).text(ui.values[0] + " - " + ui.values[1]);
      },
      change: function (event, ui) {
        table.draw();
      },
    });
    $('#' + datafor).text($(this).slider('values', 0) + ' - ' + $(this).slider('values', 1));
  });


  $.fn.dataTable.ext.search.push(
    function (settings, data, dataIndex) {
      for (var i = 0; i < filters.length; ++i) {
        var alltypes = new Set();
        var classname = filters[i][0];

        $('button.active.' + classname + '-btn').each(function (index) {
          alltypes.add($(this).attr('data-id'));
        });

        if (alltypes.size && !alltypes.has(data[filters[i][1]])) {
          return false;
        }
      }

      var bad = false;
      $(".stat-range-slider-widget").each(function (index) {
        var minvalue = $(this).slider('values', 0);
        var maxvalue = $(this).slider('values', 1);
        var col_index = column_visibility[current_vis][parseFloat($(this).attr('data-index'))];
        var stat = parseFloat(data[col_index]);
        if (stat < minvalue || stat > maxvalue) bad = true;
      });
      if (bad) return false;

      return true;
    }
  );

  var renderIcon = function (dataField, type) {
    if (type == 'display') {
      var tippy = ''
      if (dataField.title) {
        tippy = 'data-tippy-content="' + dataField.title + '"'
      }
      return '<img ' + tippy + ' height="30pt" src="' +
        dataField.icon +
        '">';
    } else return dataField.name;
  };

  var renderStat = function (dataField, type) {
    if (type == 'display') {
      var res = '';
      if (dataField.bb == '+') res = '<span class="text-primary font-weight-bold">';
      if (dataField.bb == '-') res = '<span class="text-danger font-weight-bold">';
      if (dataField.bb === '') res = '<span class="font-weight-bold">';
      return res + dataField.value.toString() + dataField.bb + '</span>';
    } else {
      return dataField.value.toString() + dataField.bb;
    }
  };

  var renderSkills = function (dataField, type) {
    var str = '';
    for (var i = 0; i < dataField.length; ++i) {
      str += '<div>' + dataField[i] + '</div>';
    }
    return str;
  };

  var table = $('#heroes-table').DataTable({
    pageLength: 50,
    ajax: "/feh/heroes_ajax.json",
    columns: [
      {
        data: 'full_name',
        render: function (dataField, type) {
          if (type == 'display') {
            return '<img height="20pt" src="' +
              dataField.icon +
              '" title="' +
              dataField.human +
              '">' +
              /*
              '<img height="30pt" src="' +
              dataField.hero_icon_url +
              '">' +
              */
              '<a href="' +
              dataField.url +
              '">' +
              dataField.name +
              ': <small>' +
              dataField.title +
              '</small>';
          } else return dataField.full_name;
        },
      },
      { data: 'f2p_level', render: renderIcon, },
      { data: 'weapon_type', render: renderIcon, },
      { data: 'movement_type', render: renderIcon, },
      { data: 'stats.0', render: renderStat, },

      { data: 'stats.1', render: renderStat, },
      { data: 'stats.2', render: renderStat, },
      { data: 'stats.3', render: renderStat, },
      { data: 'stats.4', render: renderStat, },
      { data: 'bst' },

      { data: 'max_stats.0', render: renderStat, },
      { data: 'max_stats.1', render: renderStat, },
      { data: 'max_stats.2', render: renderStat, },
      { data: 'max_stats.3', render: renderStat, },
      { data: 'max_stats.4', render: renderStat, },

      { data: 'max_bst' },
      { data: 'adjusted_stats.0', render: renderStat, },
      { data: 'adjusted_stats.1', render: renderStat, },
      { data: 'adjusted_stats.2', render: renderStat, },
      { data: 'adjusted_stats.3', render: renderStat, },

      { data: 'adjusted_stats.4', render: renderStat, },
      { data: 'adjusted_bst' },

      { data: 'generation' },
      {
        data: {
          _: 'release_date.display',
          sort: 'release_date.sortplay'
        }
      },
      { data: 'weapon_type.name' },

      { data: 'movement_type.name' },
      { data: 'f2p_level.name' },
      { data: 'book' },
      { data: 'generation' },
      { data: 'availability' },

      { data: 'skills', render: renderSkills, },
      { data: 'origin_game', render: renderIcon, },
      { data: 'stripped_name' },
      { data: 'gender' },
      { data: 'is_dancer' },

      { data: 'minmax_rating' },
      { data: 'availability_human' },
      { data: 'has_resplendent' },
      { data: 'season' },
      { data: 'harmonized_skill' },

      { data: 'artist' },
      { data: 'alias' },
      { data: 'dragonflowers' },
    ],
    columnDefs: [
      {
        "targets": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42],
        "visible": false,
      },
    ],
    stateSave: true,
  });

  $('.btn-choose-one button').click(function () {
    if (!($(this).hasClass("active"))) {
      // Deactivate everyone
      $(this).siblings().removeClass("active");
    }
    $(this).toggleClass("active");
    table.draw();
  });

  $('.btn-choose-any button').click(function () {
    $(this).toggleClass("active");
    table.draw();
  });

  $('.btn-exactly-one button').click(function () {
    // Deactivate everyone
    $(this).siblings().removeClass('active');
    $(this).toggleClass("active");
  });

  $('.btn-cycle button').click(function () {
    $(this).toggleClass("active");
    $(this).hide();
    var $next = $(this).next();
    if ($next.length) { }
    else {
      $next = $(this).siblings().first();
    }
    $next.toggleClass("active");
    $next.show();
    table.draw();
  });

  var all_columns = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21];
  $('button.statdisplay-btn').click(function () {
    for (var i = 0; i < all_columns.length; ++i) {
      var column = table.column(all_columns[i]);
      column.visible(false);
    }

    $(this).toggleClass("active");
    $(this).hide();
    var $next = $(this).next();
    if ($next.length) { }
    else {
      $next = $(this).siblings().first();
    }
    $next.toggleClass("active");
    $next.show();

    var mytype = $next.attr('data-id');
    current_vis = mytype;
    if (mytype != 'none') {
      for (var i = 0; i < column_visibility[mytype].length; ++i) {
        var column = table.column(column_visibility[mytype][i]);
        column.visible(true);
      }
    }
    table.columns.adjust().draw();
  });

  $('button.statdisplay-btn').hide();
  $('button.statdisplay-btn[data-id="normal"]').show();
  $('button.statdisplay-btn[data-id="normal"]').addClass('active');

  $("#sidebar").mCustomScrollbar({
    theme: "minimal"
  });

  $('#sidebarCollapse').on('click', function () {
    $('#sidebar, #content').toggleClass('active');
    $('.collapse.in').toggleClass('in');
    $('a[aria-expanded=true]').attr('aria-expanded', 'false');
    table.columns.adjust().draw();
  });

  $('a.toggle-vis').on('click', function (e) {
    e.preventDefault();

    // Get the column API object
    var column = table.column($(this).attr('data-column'));

    // Toggle the visibility
    column.visible(!column.visible());
  });
});
