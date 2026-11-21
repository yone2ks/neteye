// Marks the "Action" column of a DataTable so that stickyActionColumn.css can
// keep its buttons visible when a wide table scrolls horizontally.
const ACTION_COLUMN_TITLE = 'Action';
const ACTION_COLUMN_CLASS = 'dt-action-col';

function markActionColumn(table) {
    table.columns().every(function () {
        const header = $(this.header());
        if (header.text().trim() !== ACTION_COLUMN_TITLE) {
            return;
        }
        header.addClass(ACTION_COLUMN_CLASS);
        $(this.nodes()).addClass(ACTION_COLUMN_CLASS);
    });
}
