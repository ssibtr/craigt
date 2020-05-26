odoo.define('stock_barcode.picking_client_action_override', function(require) {
  'use strict';

  var core = require('web.core');
  var ClientAction = require('stock_barcode.picking_client_action');
  var ViewsWidget = require('stock_barcode.ViewsWidget');

  var _t = core._t;

  window.console.log('AAB');

  var PickingClientAction = ClientAction.extend({
    custom_events: _.extend({}, ClientAction.prototype.custom_events, {
      picking_print_delivery_slip: '_onPrintDeliverySlip',
      picking_print_picking: '_onPrintPicking',
      picking_scrap: '_onScrap',
      validate: '_onValidate',
      cancel: '_onCancel',
      put_in_pack: '_onPutInPack',
      open_package: '_onOpenPackage'
    }),

    init: function(parent, action) {
      this._super.apply(this, arguments);
      this.context = action.context;
      this.commands['O-BTN.scrap'] = this._scrap.bind(this);
      this.commands['O-BTN. '] = this._validate.bind(this);
      this.commands['O-BTN.cancel'] = this._cancel.bind(this);
      this.commands['O-BTN.pack'] = this._putInPack.bind(this);
      this.commands['O-BTN.print-slip'] = this._printDeliverySlip.bind(this);
      this.commands['O-BTN.print-op'] = this._printPicking.bind(this);
      if (!this.actionParams.pickingId) {
        this.actionParams.pickingId = action.context.active_id;
        this.actionParams.model = 'stock.picking';
      }
    },

    willStart: function() {
      var self = this;
      var res = this._super.apply(this, arguments);
      res.then(function() {
        // Get the usage of the picking type of `this.picking_id` to chose the mode between
        // `receipt`, `internal`, `delivery`.
        var picking_type_code = self.currentState.picking_type_code;
        if (picking_type_code === 'incoming') {
          self.mode = 'receipt';
        } else if (picking_type_code === 'outgoing') {
          self.mode = 'delivery';
        } else {
          self.mode = 'internal';
        }

        if (self.currentState.group_stock_multi_locations === false) {
          self.mode = 'no_multi_locations';
        }

        if (self.currentState.state === 'done') {
          self.mode = 'done';
        } else if (self.currentState.state === 'cancel') {
          self.mode = 'cancel';
        }
      });
      return res;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _getLines: function(state) {
      return state.move_line_ids;
    },

    /**
     * @override
     */
    _lot_name_used: function(product, lot_name) {
      var lines = this._getLines(this.currentState);
      for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if (
          line.qty_done !== 0 &&
          line.product_id.id === product.id &&
          (line.lot_name && line.lot_name === lot_name)
        ) {
          return true;
        }
      }
      return false;
    },

    /**
     * @override
     */
    _getPageFields: function() {
      return [
        ['location_id', 'location_id.id'],
        ['location_name', 'location_id.display_name'],
        ['location_dest_id', 'location_dest_id.id'],
        ['location_dest_name', 'location_dest_id.display_name']
      ];
    },

    /**
     * @override
     */
    _getWriteableFields: function() {
      return [
        'qty_done',
        'location_id.id',
        'location_dest_id.id',
        'lot_name',
        'lot_id.id',
        'result_package_id'
      ];
    },

    /**
     * @override
     */
    _makeNewLine: function(
      product,
      barcode,
      qty_done,
      package_id,
      result_package_id
    ) {
      var virtualId = this._getNewVirtualId();
      // var currentPage = this.pages[this.currentPageIndex]
      var currentPage = window.pageSSI;
      var newLine = {
        picking_id: this.currentState.id,
        product_id: {
          id: product.id,
          display_name: product.display_name,
          barcode: barcode,
          tracking: product.tracking
        },
        product_barcode: barcode,
        display_name: product.display_name,
        product_uom_qty: 0,
        product_uom_id: product.uom_id,
        qty_done: qty_done,
        location_id: {
          id: currentPage.location_id,
          display_name: currentPage.location_name
        },
        location_dest_id: {
          id: currentPage.location_dest_id,
          display_name: currentPage.location_dest_name
        },
        package_id: package_id,
        result_package_id: result_package_id,
        state: 'assigned',
        reference: this.name,
        virtual_id: virtualId
      };
      return newLine;
    },

    /**
     * Makes the rpc to `button_validate`.
     * This method could open a wizard so it takes care of removing/adding the "barcode_scanned"
     * event listener.
     *
     * @private
     * @returns {Deferred}
     */
    _validate: function() {
      var self = this;
      window.console.log('B');
      this.mutex.exec(function() {
        var getAttachment = function(self) {
          window.console.log('C');
          var domain = [
            ['res_model', '=', 'stock.picking'],
            ['res_id', '=', self.actionParams.pickingId]
          ];
          window.console.log('Cbis');
          self
            ._rpc({
              model: 'ir.attachment',
              method: 'search',
              args: [domain]
            })
            .then(response => {
              window.console.log('D');
              if (response.length > 0) {
                response.forEach(res => {
                  window.console.log(res);
                  return window.open(`/web/content/${res}?download=true`);
                });
              }
              return window.console.log('RESPONSE', response);
            });
        };
        return self._save().then(function() {
          return self
            ._rpc({
              model: self.actionParams.model,
              method: 'button_validate',
              args: [[self.actionParams.pickingId]]
            })
            .then(function(res) {
              var def = $.when();
              var backorder = false;
              var exitCallback = function(infos) {
                if (infos !== 'special') {
                  self.do_notify(
                    _t('Success'),
                    _t('The transfer has been validated')
                  );
                  if (backorder === true) {
                    backorder = false;
                    getAttachment(self);
                  }
                  setTimeout(function() {
                    self.trigger_up('exit');
                  }, 1000);
                }
                core.bus.on(
                  'barcode_scanned',
                  self,
                  self._onBarcodeScannedHandler
                );
              };
              window.console.log('E');
              if (_.isObject(res)) {
                backorder = true;
                window.console.log('OPTION #1');
                var options = {
                  on_close: exitCallback
                };
                return def.then(function() {
                  backorder = true;
                  core.bus.off(
                    'barcode_scanned',
                    self,
                    self._onBarcodeScannedHandler
                  );
                  setTimeout(function() {
                    return self.do_action(res, options);
                  }, 1000);
                });
              } else {
                return def.then(function() {
                  window.console.log('OPTION #2');
                  getAttachment(self);
                  setTimeout(function() {
                    return exitCallback();
                  }, 1000);
                });
              }
            });
        });
      });
    },

    /**
     * Makes the rpc to `action_cancel`.
     *
     * @private
     */
    _cancel: function() {
      var self = this;
      this.mutex.exec(function() {
        return self._save().then(function() {
          return self
            ._rpc({
              model: self.actionParams.model,
              method: 'action_cancel',
              args: [[self.actionParams.pickingId]]
            })
            .then(function() {
              self.do_notify(
                _t('Cancel'),
                _t('The transfer has been cancelled')
              );
              self.trigger_up('exit');
            });
        });
      });
    },

    /**
     * Makes the rpc to `button_scrap`.
     * This method opens a wizard so it takes care of removing/adding the "barcode_scanned" event
     * listener.
     *
     * @private
     */
    _scrap: function() {
      var self = this;
      this.mutex.exec(function() {
        return self._save().then(function() {
          return self
            ._rpc({
              model: 'stock.picking',
              method: 'button_scrap',
              args: [[self.actionParams.pickingId]]
            })
            .then(function(res) {
              var exitCallback = function() {
                core.bus.on(
                  'barcode_scanned',
                  self,
                  self._onBarcodeScannedHandler
                );
              };
              var options = {
                on_close: exitCallback
              };
              core.bus.off(
                'barcode_scanned',
                self,
                self._onBarcodeScannedHandler
              );
              return self.do_action(res, options);
            });
        });
      });
    },

    /**
     * @override
     */
    _applyChanges: function(changes) {
      var formattedCommands = [];
      var cmd = [];
      for (var i in changes) {
        var line = changes[i];
        if (line.id) {
          // Line needs to be updated
          cmd = [
            1,
            line.id,
            {
              qty_done: line.qty_done,
              location_id: line.location_id.id,
              location_dest_id: line.location_dest_id.id,
              lot_id: line.lot_id && line.lot_id[0],
              lot_name: line.lot_name,
              package_id: line.package_id ? line.package_id[0] : false,
              result_package_id: line.result_package_id
                ? line.result_package_id[0]
                : false
            }
          ];
          formattedCommands.push(cmd);
        } else {
          // Line needs to be created
          cmd = [
            0,
            0,
            {
              picking_id: line.picking_id,
              product_id: line.product_id.id,
              product_uom_id: line.product_uom_id[0],
              qty_done: line.qty_done,
              location_id: line.location_id.id,
              location_dest_id: line.location_dest_id.id,
              lot_name: line.lot_name,
              lot_id: line.lot_id && line.lot_id[0],
              state: 'assigned',
              package_id: line.package_id ? line.package_id[0] : false,
              result_package_id: line.result_package_id
                ? line.result_package_id[0]
                : false,
              dummy_id: line.virtual_id
            }
          ];
          formattedCommands.push(cmd);
        }
      }
      if (formattedCommands.length > 0) {
        var params = {
          mode: 'write',
          model_name: this.actionParams.model,
          record_id: this.currentState.id,
          write_vals: formattedCommands,
          write_field: 'move_line_ids'
        };
        return this._rpc({
          route: '/stock_barcode/get_set_barcode_view_state',
          params: params
        });
      } else {
        return $.Deferred().reject();
      }
    },

    /**
     * @override
     */
    _showInformation: function() {
      var self = this;
      return this._super.apply(this, arguments).then(function() {
        if (self.formWidget) {
          self.formWidget.destroy();
        }
        self.linesWidget.destroy();
        self.ViewsWidget = new ViewsWidget(
          self,
          'stock.picking',
          'stock_barcode.stock_picking_barcode',
          {},
          { currentId: self.currentState.id },
          'readonly'
        );
        self.ViewsWidget.appendTo(self.$el);
      });
    },

    /**
     *
     */
    _putInPack: function() {
      var self = this;
      this.mutex.exec(function() {
        return self._save().then(function() {
          return self
            ._rpc({
              model: 'stock.picking',
              method: 'put_in_pack',
              args: [[self.actionParams.pickingId]],
              kwargs: { context: self.context }
            })
            .then(function(res) {
              var def = $.when();
              self._endBarcodeFlow();
              if (res.type && res.type === 'ir.actions.act_window') {
                var exitCallback = function(infos) {
                  if (infos !== 'special') {
                    self.trigger_up('reload');
                  }
                  core.bus.on(
                    'barcode_scanned',
                    self,
                    self._onBarcodeScannedHandler
                  );
                };
                var options = {
                  on_close: exitCallback
                };
                return def.then(function() {
                  core.bus.off(
                    'barcode_scanned',
                    self,
                    self._onBarcodeScannedHandler
                  );
                  return self.do_action(res, options);
                });
              } else {
                return def.then(function() {
                  return self.trigger_up('reload');
                });
              }
            });
        });
      });
    },

    /**
     * Handles the `open_package` OdooEvent. It hides the main widget and
     * display a standard kanban view with all quants inside the package.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onOpenPackage: function(ev) {
      var self = this;

      ev.stopPropagation();
      this.linesWidget.destroy();
      this.headerWidget.toggleDisplayContext('specialized');

      var virtual_id = _.isString(ev.data.id) ? ev.data.id : false;
      this.mutex.exec(function() {
        return self._save().then(function() {
          var currentPage = self.pages[self.currentPageIndex];
          var id = ev.data.id;
          if (virtual_id) {
            var rec = _.find(currentPage.lines, function(line) {
              return line.dummy_id === virtual_id;
            });
            id = rec.id;
          }
          var package_id = _.find(currentPage.lines, function(line) {
            return line.id === id;
          });
          package_id = package_id.package_id[0];

          var params = { domain: [['package_id', '=', package_id]] };
          self.ViewsWidget = new ViewsWidget(
            self,
            'stock.quant',
            'stock_barcode.stock_quant_barcode_kanban',
            {},
            params,
            false,
            'kanban'
          );
          return self.ViewsWidget.appendTo(self.$el);
        });
      });
    },

    _printPicking: function() {
      var self = this;
      this.mutex.exec(function() {
        return self._save().then(function() {
          return self
            ._rpc({
              model: 'stock.picking',
              method: 'do_print_picking',
              args: [[self.actionParams.pickingId]]
            })
            .then(function(res) {
              return self.do_action(res);
            });
        });
      });
    },

    _printDeliverySlip: function() {
      var self = this;
      this.mutex.exec(function() {
        return self._save().then(function() {
          return self.do_action(self.currentState.actionReportDeliverySlipId, {
            additional_context: {
              active_id: self.actionParams.pickingId,
              active_ids: [self.actionParams.pickingId],
              active_model: 'stock.picking'
            }
          });
        });
      });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handles the `validate` OdooEvent. It makes an RPC call
     * to the method 'button_validate' to validate the current picking
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onValidate: function(ev) {
      ev.stopPropagation();
      this._validate();
    },

    /**
     * Handles the `cancel` OdooEvent. It makes an RPC call
     * to the method 'action_cancel' to cancel the current picking
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onCancel: function(ev) {
      ev.stopPropagation();
      this._cancel();
    },

    /**
     * Handles the `print_picking` OdooEvent. It makes an RPC call
     * to the method 'do_print_picking'.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onPrintPicking: function(ev) {
      ev.stopPropagation();
      this._printPicking();
    },

    /**
     * Handles the `print_delivery_slip` OdooEvent. It makes an RPC call
     * to the method 'do_action' on a 'ir.action_window' with the additional context
     * needed
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onPrintDeliverySlip: function(ev) {
      ev.stopPropagation();
      this._printDeliverySlip();
    },

    /**
     * Handles the `scan` OdooEvent. It makes an RPC call
     * to the method 'button_scrap' to scrap a picking.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onScrap: function(ev) {
      ev.stopPropagation();
      this._scrap();
    },

    /**
     * Handles the `Put in pack` OdooEvent. It makes an RPC call
     * to the method 'put_in_pack' to create a pack and link move lines to it.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onPutInPack: function(ev) {
      ev.stopPropagation();
      this._putInPack();
    }
  });

  //   window.console.log(PickingClientAction);

  core.action_registry.add(
    'stock_barcode_picking_client_action',
    PickingClientAction
  );

  return PickingClientAction;
});

odoo.define('stock_barcode.LinesWidget_override', function(require) {
  'use strict';

  var core = require('web.core');

  var linesOld = require('stock_barcode.LinesWidget');

  var QWeb = core.qweb;

  linesOld.include({
    _highlightLine: function($line, doNotClearLineHighlight) {
      var $body = this.$el.filter('.o_barcode_lines');
      if (!doNotClearLineHighlight) {
        this.clearLineHighlight();
      }
      // Highlight `$line`.
      $line.toggleClass('o_highlight', true);
      $line.parents('.o_barcode_lines').toggleClass('o_js_has_highlight', true);

      var isReservationProcessed;
      if (
        $line
          .find('.o_barcode_scanner_qty')
          .text()
          .indexOf('/') === -1
      ) {
        isReservationProcessed = false;
      } else {
        isReservationProcessed = this._isReservationProcessedLine($line);
      }
      if (isReservationProcessed === 1) {
        $line.toggleClass('o_highlight_green', false);
        $line.toggleClass('o_highlight_red', true);
      } else {
        $line.toggleClass('o_highlight_green', true);
        $line.toggleClass('o_highlight_red', false);
      }

      // Scroll to `$line`.
      try {
        $body.animate(
          {
            scrollTop:
              $body.scrollTop() +
              $line.position().top -
              $body.height() / 2 +
              $line.height() / 2
          },
          500
        );
      } catch (error) {
        console.log(error);
      }
		},
    _renderLines: function() {
      if (this.mode === 'done') {
        if (this.model === 'stock.picking') {
          this._toggleScanMessage('picking_already_done');
        } else if (this.model === 'stock.inventory') {
          this._toggleScanMessage('inv_already_done');
        }
        return;
      } else if (this.mode === 'cancel') {
        this._toggleScanMessage('picking_already_cancelled');
        return;
      }
      //          CUSTOM
      this.page = window.pageSSI;
      this.pageIndex = 0;
      window.console.log('Chad');
      console.log(this);

      // Render and append the page summary.
      var $header = this.$el.filter('.o_barcode_lines_header');
      var $pageSummary = $(
        QWeb.render('stock_barcode_summary_template', {
          locationName: this.page.location_name,
          locationDestName: this.page.location_dest_name,
          nbPages: this.nbPages,
          pageIndex: this.pageIndex + 1,
          mode: this.mode,
          model: this.model
        })
      );
      $header.append($pageSummary);

      // Render and append the lines, if any.
      var $body = this.$el.filter('.o_barcode_lines');
      if (this.page.lines.length) {
        var $lines = $(
          QWeb.render('stock_barcode_lines_template', {
            lines: this.getProductLines(this.page.lines),
            packageLines: this.getPackageLines(this.page.lines),
            model: this.model,
            groups: this.groups
          })
        );
        $body.prepend($lines);
        $lines.on('click', '.o_edit', this._onClickEditLine.bind(this));
        $lines.on(
          'click',
          '.o_package_content',
          this._onClickTruckLine.bind(this)
        );
      }
      // Toggle and/or enable the control buttons. At first, they're all displayed and enabled.
      var $next = this.$('.o_next_page');
      var $previous = this.$('.o_previous_page');
      var $validate = this.$('.o_validate_page');
      if (this.nbPages === 1) {
        $next.prop('disabled', true);
        $previous.prop('disabled', true);
      }
      if (this.pageIndex + 1 === this.nbPages) {
        $next.toggleClass('o_hidden');
        $next.prop('disabled', true);
      } else {
        $validate.toggleClass('o_hidden');
      }

      if (!this.page.lines.length) {
        $validate.prop('disabled', true);
      }

      this._handleControlButtons();

      if (this.mode === 'receipt') {
        this._toggleScanMessage('scan_products');
      } else if (['delivery', 'inventory'].indexOf(this.mode) >= 0) {
        this._toggleScanMessage('scan_src');
      } else if (this.mode === 'internal') {
        this._toggleScanMessage('scan_src');
      } else if (this.mode === 'no_multi_locations') {
        this._toggleScanMessage('scan_products');
      }

      var $summary_src = this.$('.o_barcode_summary_location_src');
      var $summary_dest = this.$('.o_barcode_summary_location_dest');

      if (this.mode === 'receipt') {
        $summary_dest.toggleClass('o_barcode_summary_location_highlight', true);
      } else if (this.mode === 'delivery' || this.mode === 'internal') {
        $summary_src.toggleClass('o_barcode_summary_location_highlight', true);
      }
    }
  });
});

odoo.define('stock_barcode.ClientAction_Override', function(require) {
  'use strict';

  var ClientActionOld = require('stock_barcode.ClientAction');
  window.console.log('TEST CALLED');
  var ClientActionOld = require('stock_barcode.ClientAction');
  var utils = require('web.utils');
  var LinesWidget = require('stock_barcode.LinesWidget');
  var ViewsWidget = require('stock_barcode.ViewsWidget');

  ClientActionOld.include({
    _onEditLine: function(ev) {
      ev.stopPropagation();
      if (window.pagesSSI) {
        this.pages = window.pagesSSI;
      } else {
        this.pages = [];
      }
      this.currentPageIndex = 0;

      this.linesWidgetState = this.linesWidget.getState();
      this.linesWidget.destroy();
      this.headerWidget.toggleDisplayContext('specialized');

      // If we want to edit a not yet saved line, keep its virtual_id to match it with the result
      // of the `applyChanges` RPC.
      var virtual_id = _.isString(ev.data.id) ? ev.data.id : false;

      var self = this;
      this.mutex.exec(function() {
        return self._save().then(function() {
          var id = ev.data.id;
          if (virtual_id) {
            var currentPage = self.pages[self.currentPageIndex];
            var rec = _.find(currentPage.lines, function(line) {
              return line.dummy_id === virtual_id;
            });
            id = rec.id;
          }

          if (self.actionParams.model === 'stock.picking') {
            self.ViewsWidget = new ViewsWidget(
              self,
              'stock.move.line',
              'stock_barcode.stock_move_line_product_selector',
              {},
              { currentId: id }
            );
          } else {
            self.ViewsWidget = new ViewsWidget(
              self,
              'stock.inventory.line',
              'stock_barcode.stock_inventory_line_barcode',
              {},
              { currentId: id }
            );
          }
          return self.ViewsWidget.appendTo(self.$el);
        });
      });
    },

    _step_source: function(barcode, linesActions) {
      if (window.pagesSSI) {
        this.pages = window.pagesSSI;
      } else {
        this.pages = [];
      }
      this.currentPageIndex = 0;

      this.currentStep = 'source';
      var errorMessage;

      /* Bypass this step in the following cases:
         - the picking is a receipt
         - the multi location group isn't active
      */
      var sourceLocation = this.locationsByBarcode[barcode];
      if (
        sourceLocation &&
        !(this.mode === 'receipt' || this.mode === 'no_multi_locations')
      ) {
        if (!isChildOf(this.currentState.location_id, sourceLocation)) {
          errorMessage = _t(
            'This location is not a child of the main location.'
          );
          return $.Deferred().reject(errorMessage);
        } else {
          // There's nothing to do on the state here, just mark `this.scanned_location`.
          linesActions.push([this.linesWidget.highlightLocation, [true]]);
          if (this.actionParams.model === 'stock.picking') {
            linesActions.push([
              this.linesWidget.highlightDestinationLocation,
              [false]
            ]);
          }
          this.scanned_location = sourceLocation;
          this.currentStep = 'product';
          return $.when({ linesActions: linesActions });
        }
      }
      /* Implicitely set the location source in the following cases:
          - the user explicitely scans a product
          - the user explicitely scans a lot
          - the user explicitely scans a package
      */
      // We already set the scanned_location even if we're not sure the
      // following steps will succeed. They need scanned_location to work.
      this.scanned_location = {
        id: this.pages
          ? this.pages[this.currentPageIndex].location_id
          : this.currentState.location_id.id,
        display_name: this.pages
          ? this.pages[this.currentPageIndex].location_name
          : this.currentState.location_id.display_name
      };
      linesActions.push([this.linesWidget.highlightLocation, [true]]);
      if (this.actionParams.model === 'stock.picking') {
        linesActions.push([
          this.linesWidget.highlightDestinationLocation,
          [false]
        ]);
      }

      return this._step_product(barcode, linesActions).then(
        function(res) {
          return $.when({ linesActions: res.linesActions });
        },
        function(specializedErrorMessage) {
          delete this.scanned_location;
          this.currentStep = 'source';
          if (specializedErrorMessage) {
            return $.Deferred().reject(specializedErrorMessage);
          }
          var errorMessage = _t('You are expected to scan a source location.');
          return $.Deferred().reject(errorMessage);
        }
      );
    },

    _incrementLines: function(params) {
      if (window.pagesSSI) {
        this.pages = window.pagesSSI;
      } else {
        this.pages = [];
      }
      this.currentPageIndex = 0;
      var line = this._findCandidateLineToIncrement(params);
      var isNewLine = false;
      // CUSTOM
      if (!line) {
        alert('You cannot increment quantity on this product');
        return {
          id: 0,
          virtualId: 0,
          lineDescription: { top: '0' },
          isNewLine: false,
          top: 0
        };
      }
      if (line) {
        // Update the line with the processed quantity.
        if (
          params.product.tracking === 'none' ||
          params.lot_id ||
          params.lot_name
        ) {
          if (this.actionParams.model === 'stock.picking') {
            line.qty_done += params.product.qty || 1;
          } else if (this.actionParams.model === 'stock.inventory') {
            line.product_qty += params.product.qty || 1;
          }
        }
      } else {
        isNewLine = true;
        // Create a line with the processed quantity.
        if (
          params.product.tracking === 'none' ||
          params.lot_id ||
          params.lot_name
        ) {
          line = this._makeNewLine(
            params.product,
            params.barcode,
            params.product.qty || 1,
            params.package_id,
            params.result_package_id
          );
        } else {
          line = this._makeNewLine(
            params.product,
            params.barcode,
            0,
            params.package_id,
            params.result_package_id
          );
        }
        this._getLines(this.currentState).push(line);
        this.pages[this.currentPageIndex].lines.push(line);
      }
      if (this.actionParams.model === 'stock.picking') {
        if (params.lot_id) {
          line.lot_id = [params.lot_id];
        }
        if (params.lot_name) {
          line.lot_name = params.lot_name;
        }
      } else if (this.actionParams.model === 'stock.inventory') {
        if (params.lot_id) {
          line.prod_lot_id = [params.lot_id, params.lot_name];
        }
      }
      return {
        id: line.id,
        virtualId: line.virtual_id,
        lineDescription: line,
        isNewLine: isNewLine
      };
    },
    _save: function(params) {
      if (window.pagesSSI) {
        this.pages = window.pagesSSI;
      } else {
        this.pages = [];
      }
      this.currentPageIndex = 0;

      params = params || {};
      var self = this;

      // keep a reference to the currentGroup
      var currentPage = this.pages[this.currentPageIndex];
      if (!currentPage) {
        currentPage = {};
      }
      var currentLocationId = currentPage.location_id;
      var currentLocationDestId = currentPage.location_dest_id;

      // make a write with the current changes
      var recordId =
        this.actionParams.pickingId || this.actionParams.inventoryId;
      var applyChangesDef = this._applyChanges(this._compareStates()).then(
        function(state) {
          // Fixup virtual ids in `self.scanned_lines`
          var virtual_ids_to_fixup = _.filter(
            self._getLines(state[0]),
            function(line) {
              return line.dummy_id;
            }
          );
          _.each(virtual_ids_to_fixup, function(line) {
            if (self.scannedLines.indexOf(line.dummy_id) !== -1) {
              self.scannedLines = _.without(self.scannedLines, line.dummy_id);
              self.scannedLines.push(line.id);
            }
          });

          return self._getState(recordId, state);
        },
        function() {
          if (params.forceReload) {
            return self._getState(recordId);
          } else {
            return $.when();
          }
        }
      );

      return applyChangesDef.then(function() {
        self.pages = self._makePages();

        var newPageIndex =
          _.findIndex(self.pages, function(page) {
            return (
              page.location_id ===
                (params.new_location_id || currentLocationId) &&
              (self.actionParams.model === 'stock.inventory' ||
                page.location_dest_id ===
                  (params.new_location_dest_id || currentLocationDestId))
            );
          }) || 0;
        if (newPageIndex === -1) {
          newPageIndex = 0;
        }
        self.currentPageIndex = newPageIndex;
      });
    },
    _reloadLineWidget: function(pageIndex) {
      if (window.pagesSSI) {
        this.pages = window.pagesSSI;
      } else {
        this.pages = [];
      }
      this.currentPageIndex = 0;
      if (this.linesWidget) {
        this.linesWidget.destroy();
      }
      var nbPages = this.pages.length;
      var preparedPage = $.extend(true, {}, this.pages[pageIndex]);
      this.linesWidget = new LinesWidget(
        this,
        preparedPage,
        pageIndex,
        nbPages
      );
      this.linesWidget.appendTo(this.$el);
      // In some cases, we want to restore the GUI state of the linesWidget
      // (on a reload not calling _endBarcodeFlow)
      if (this.linesWidgetState) {
        this.linesWidget.highlightLocation(
          this.linesWidgetState.highlightLocationSource
        );
        this.linesWidget.highlightDestinationLocation(
          this.linesWidgetState.highlightLocationDestination
        );
        this.linesWidget._toggleScanMessage(this.linesWidgetState.scan_message);
        delete this.linesWidgetState;
      }
      if (this.lastScannedPackage) {
        this.linesWidget.highlightPackage(this.lastScannedPackage);
        delete this.lastScannedPackage;
      }
    },
    _onExit: function(ev) {
      ev.stopPropagation();
      var self = this;
      this.mutex.exec(function() {
        return self._save().then(function() {
          self.actionManager.$el.height(self.actionManagerInitHeight);
          self.trigger_up('history_back');
        });
      });
    },
    _makePages: function() {
      window.console.log('METHOD CALLED');
      var pages = [];
      var defaultPage = {};
      var self = this;
      if (this._getLines(this.currentState).length) {
        // from https://stackoverflow.com/a/25551041
        var groups = _.groupBy(this._getLines(this.currentState), function(
          line
        ) {
          return _.map(self._getPageFields(), function(field) {
            return utils.into(line, field[1]);
          }).join('#');
        });
        var array = [];
        pages = _.map(groups, function(group) {
          var page = {};
          _.map(self._getPageFields(), function(field) {
            page[field[0]] = utils.into(group[0], field[1]);
          });
          page.lines = group;
          return page;
        });
      } else {
        _.each(self._getPageFields(), function(field) {
          defaultPage[field[0]] = utils.into(self.currentState, field[1]);
        });
        defaultPage.lines = [];
      }
      pages = _.sortBy(pages, 'location_name');

      //          CUSTOM
      window, console.log('OLD PAGES', pages);
      var obj = {
        lines: [],
        location_dest_id: 1,
        location_dest_name: '',
        location_id: 1,
        location_name: '',
        dummy_id: 1
      };
      var array = [];
      _.each(pages, function(page) {
        _.each(page.lines, function(line) {
          obj.lines.push(line);
        });
        obj.location_dest_id = page.location_dest_id;
        obj.location_dest_name = page.location_dest_name;
        obj.location_id = page.location_id;
        obj.location_name = page.location_name;
      });
      array.push(obj);
      // window.console.log(array)
      pages = array;
      window.console.log('NEW PAGES', pages);

      // Create a new page if the pair scanned location / default destination location doesn't
      // exist yet and the scanned location isn't the one of current page.
      var currentPage = window.pageSSI;
      if (
        this.scanned_location &&
        currentPage.location_id !== this.scanned_location.id
      ) {
        var alreadyInPages = _.find(pages, function(page) {
          return (
            page.location_id === self.scanned_location.id &&
            (self.actionParams.model === 'stock.inventory' ||
              page.location_dest_id === self.currentState.location_dest_id.id)
          );
        });
        if (!alreadyInPages) {
          var pageValues = {
            location_id: this.scanned_location.id,
            location_name: this.scanned_location.display_name,
            lines: []
          };
          if (self.actionParams.model === 'stock.picking') {
            pageValues.location_dest_id = this.currentState.location_dest_id.id;
            pageValues.location_dest_name = this.currentState.location_dest_id.display_name;
          }
          pages.push(pageValues);
        }
      }

      if (pages.length === 0) {
        pages.push(defaultPage);
      }

      //          CUSTOM
      window.pageSSI = pages[0];
      window.pagesSSI = pages;
      return pages;
    },
    _findCandidateLineToIncrement: function(params) {
      var product = params.product;
      var lotId = params.lot_id;
      var lotName = params.lot_name;
      var packageId = params.package_id;
      //                this.pages = window.pageSSI

      //         var currentPage = this.pages[this.currentPageIndex];
      var currentPage = window.pageSSI;
      var res = false;
      for (var z = 0; z < currentPage.lines.length; z++) {
        var lineInCurrentPage = currentPage.lines[z];
        if (lineInCurrentPage.product_id.id === product.id) {
          // If the line is empty, we could re-use it.
          if (
            (lineInCurrentPage.virtual_id &&
              (this.actionParams.model === 'stock.picking' &&
                !lineInCurrentPage.qty_done &&
                !lineInCurrentPage.product_uom_qty &&
                !lineInCurrentPage.lot_id &&
                !lineInCurrentPage.lot_name &&
                !lineInCurrentPage.package_id)) ||
            (this.actionParams.model === 'stock.inventory' &&
              !lineInCurrentPage.product_qty &&
              !lineInCurrentPage.prod_lot_id)
          ) {
            res = lineInCurrentPage;
            break;
          }

          if (
            product.tracking === 'serial' &&
            ((this.actionParams.model === 'stock.picking' &&
              lineInCurrentPage.qty_done > 0) ||
              (this.actionParams.model === 'stock.inventory' &&
                lineInCurrentPage.product_qty > 0))
          ) {
            continue;
          }
          if (
            lineInCurrentPage.qty_done &&
            (this.actionParams.model === 'stock.inventory' ||
              lineInCurrentPage.location_dest_id.id ===
                currentPage.location_dest_id) &&
            this.scannedLines.indexOf(
              lineInCurrentPage.virtual_id || lineInCurrentPage.id
            ) === -1 &&
            lineInCurrentPage.qty_done >= lineInCurrentPage.product_uom_qty
          ) {
            continue;
          }
          if (
            lotId &&
            ((this.actionParams.model === 'stock.picking' &&
              lineInCurrentPage.lot_id &&
              lineInCurrentPage.lot_id[0] !== lotId) ||
              (this.actionParams.model === 'stock.inventory' &&
                lineInCurrentPage.prod_lot_id &&
                lineInCurrentPage.prod_lot_id[0] !== lotId))
          ) {
            continue;
          }
          if (
            lotName &&
            lineInCurrentPage.lot_name &&
            lineInCurrentPage.lot_name !== lotName
          ) {
            continue;
          }
          if (
            packageId &&
            (!lineInCurrentPage.package_id ||
              lineInCurrentPage.package_id.id !== packageId[0])
          ) {
            continue;
          }
          if (
            lineInCurrentPage.product_uom_qty &&
            lineInCurrentPage.qty_done >= lineInCurrentPage.product_uom_qty
          ) {
            continue;
          }
          res = lineInCurrentPage;
          break;
        }
      }
      return res;
    }
  });
});
