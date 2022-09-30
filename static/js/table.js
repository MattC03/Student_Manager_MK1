$(document).ready(function () {
    $('#main_table').DataTable({
        order: [[3, 'desc']],
    });

    $('#main_table tbody').on('mouseenter', 'td', function () {
        var colIdx = table.cell(this).index().column;

        $(table.cells().nodes()).removeClass('highlight');
        $(table.column(colIdx).nodes()).addClass('highlight');
    });
});