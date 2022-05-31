$(document).ready(function () {
  $('button.max-btn[data-id="True"]').addClass('active');

  var filters = [
    ['max', 9],
    ['prf', 10],
    ['f2p', 11],
    ['slot', 12],
    ['book', 13],
    ['weapon_permissions', 15],
    ['movement_permissions', 16],
  ];

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

        if (alltypes.size && (filters[i][0] == 'f2p' ||
          filters[i][0] == 'weapon_permissions' ||
          filters[i][0] == 'movement_permissions')) {
          var found = false;
          var datum = data[filters[i][1]];
          for (let item of alltypes) {
            if (datum.includes(item)) {
              found = true;
              break;
            }
          }
          if (!found) return false;
        } else if (alltypes.size && !alltypes.has(data[filters[i][1]])) {
          return false;
        }
      }

      var bad = false;
      $(".stat-range-slider-widget").each(function (index) {
        var minvalue = $(this).slider('values', 0);
        var maxvalue = $(this).slider('values', 1);
        var col_index = parseFloat($(this).attr('data-index'));
        var stat = parseFloat(data[col_index]);
        if (stat < minvalue || stat > maxvalue) bad = true;
      });
      if (bad) return false;

      return true;
    }
  );

  function format(d) {
    var res = '';
    if (d.usablebyicons.length) {
      res += '<p>Usable by: ';
      for (var i = 0; i < d.usablebyicons.length; ++i) {
        res += '<img height="30pt" src="' + d.usablebyicons[i] + '">';
      }
      res += '</p>';
    }
    res += '<p>';
    res += '<span style="white-space: pre-line">' + d.description + '</span>';
    res += '</p>';

    res += '<p>';
    for (var i = 0; i < d.heroes.length; ++i) {
      res += '<img height="20pt" src="' + d.heroes[i][0] + '">';
      res += '<img height="20pt" src="' + d.heroes[i][1] + '">';
      res += d.heroes[i][3] + ': ';
      res += d.heroes[i][2] + '<br/>';
    }
    res += '</p>';
    return res;
  }

  var table = $('#heroes-table').DataTable({
    pageLength: 50,
    ajax: SKILLS_AJAX_URL,
    columns: [
      { data: 'detailscontrol' },
      {
        data: 'name',
        render: function (dataField, type) {
          if (type == 'display') {
            return '<a href="' + dataField.url + '">' + dataField.name + '</a>';
          } else return dataField.name;
        },
      },
      {
        data: 'slot',
        render: function (dataField, type) {
          if (type == 'display') {
            return '<img height="30pt" src="' + dataField.icon + '">';
          } else return dataField.name;
        },
      },
      { data: 'cost' },
      {
        data: 'icons',
        render: function (dataField, type) {
          if (type == 'display') {
            var res = '';
            for (var i = 0; i < dataField.length; ++i) {
              res += '<img height="30pt" src="' + dataField[i] + '">';
            }
            return res;
          } else return dataField;
        },
      },

      { data: 'rarity' },
      {
        data: {
          _: 'release_date.display',
          sort: 'release_date.sortplay'
        }
      },
      {
        data: 'heroes',
        render: function (dataField, type) {
          if (type == 'display') {
            var res = '';
            for (var i = 0; i < dataField.length; ++i) {
              res += '<img height="20pt" src="' + dataField[i][0] + '">';
              res += '<img height="20pt" src="' + dataField[i][1] + '">';
              res += dataField[i][3] + ': ';
              res += dataField[i][2] + '<br/>';
            }
            return res;
          } else return dataField;
        },
      },
      {
        data: 'description',
        render: function (dataField, type) {
          if (type == 'display') {
            return '<span style="white-space: pre-line">' + dataField + '</span>';
          } else return dataField;
        },
      },
      { data: 'is_max' },
      { data: 'is_prf' },
      { data: 'f2p_levels' },
      { data: 'slot.name' },
      { data: 'book' },
      {
        data: 'usablebyicons',
        render: function (dataField, type) {
          if (type == 'display') {
            var res = 'Usable by: ';
            for (var i = 0; i < dataField.length; ++i) {
              res += '<img height="30pt" src="' + dataField[i] + '">';
            }
            return res;
          } else return '';
        },
      },
      { data: 'weapon_permissions' },
      { data: 'movement_permissions' },
      { data: 'stripped_name' },
      {
        data: 'hero_stripped_names',
        render: function (dataField, type) {
          var res = '';
          for (var i = 0; i < dataField.length; ++i) {
            res += dataField[i];
          }
          return res;
        },
      }
    ],
    columnDefs: [
      {
        targets: [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
        visible: false,
      },
      {
        className: "details-control",
        targets: [0]
      },
    ],
    stateSave: true,
  });

  // Add event listener for opening and closing details
  $('tbody').on('click', 'td.details-control', function () {
    var tr = $(this).closest('tr');
    var row = table.row(tr);

    if (row.child.isShown()) {
      // This row is already open - close it
      row.child.hide();
      tr.removeClass('shown');
    }
    else {
      // Open this row
      row.child(format(row.data())).show();
      tr.addClass('shown');
    }
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
