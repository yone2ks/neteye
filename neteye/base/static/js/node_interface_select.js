/**
 * Fetch interfaces belonging to the given node and populate a <select> element.
 *
 * @param {string|number} nodeId          Node primary key.
 * @param {string}        targetId        ID of the <select> to populate (without '#').
 * @param {Object}        [opts]
 * @param {string}        [opts.valueKey='id']      Property to use as the option value.
 * @param {string}        [opts.textKey='name']     Property to use as the option label.
 * @param {function}      [opts.textFn]             function(intf) -> string; overrides textKey when provided.
 * @param {function}      [opts.filter]             function(intf) -> bool; falsy items are skipped.
 * @param {*}             [opts.selectedValue]      Pre-select the option whose value matches this.
 */
function loadInterfaces(nodeId, targetId, opts) {
    opts = opts || {};
    var valueKey      = opts.valueKey || 'id';
    var textKey       = opts.textKey  || 'name';
    var textFn        = opts.textFn   || null;
    var filter        = opts.filter   || null;
    var selectedValue = (opts.selectedValue !== undefined && opts.selectedValue !== null)
                        ? String(opts.selectedValue) : null;

    $.ajax({
        url: '/api/interfaces/filter?field=node_id&filter_str=' + nodeId,
        type: 'GET',
        success: function (interfaces) {
            var $target = $('#' + targetId);
            // Destroy Select2 before clearing to avoid stale dropdown state
            if ($target.hasClass('select2-hidden-accessible')) {
                $target.select2('destroy');
            }
            $target.empty();
            for (var i = 0; i < interfaces.length; i++) {
                var intf = interfaces[i];
                if (filter && !filter(intf)) { continue; }
                var label = textFn ? textFn(intf) : intf[textKey];
                var isSelected = (selectedValue !== null &&
                                  String(intf[valueKey]) === selectedValue);
                $target.append(
                    $('<option></option>')
                        .attr('value', intf[valueKey])
                        .prop('selected', isSelected)
                        .text(label)
                );
            }
            // Reinitialize Select2 if it was previously applied
            if ($.fn.select2 && $target.data('select2-init')) {
                $target.select2({ theme: 'bootstrap4', width: '100%' });
            }
        }
    });
}
