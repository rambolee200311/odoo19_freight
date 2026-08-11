/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { getDefaultConfig } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { useDebounced } from "@web/core/utils/timing";
import { session } from "@web/session";
import { Domain } from "@web/core/domain";
import { sprintf } from "@web/core/utils/strings";

const { Component, useSubEnv, useState, onMounted, onWillStart, useRef } = owl;
import { loadJS, loadCSS } from "@web/core/assets"

class FreightDashboard extends Component {
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");

    this.state = useState({
      freightStats: {
        // Statics
        'total_shipment': 0,
        'pending_quat': 0,
        'pending_booking': 0,
        'total_port': 0,
        'shipper_count': 0,
        'consignee_count': 0,
        // Shipment
        'direct_count': 0,
        'house_count': 0,
        'master_count': 0,
        'air': 0,
        'ocean': 0,
        'land': 0,
      },
    });

    useSubEnv({
      config: {
        ...getDefaultConfig(),
        ...this.env.config,
      },
    });
    this.freightDirection = useRef('freightDirection');
    this.freightStages = useRef('freightStages');
    this.moveType = useRef('moveType');
    this.shipmentMonth = useRef('shipmentMonth');
    this.topConsignee = useRef('topConsignee');
    this.topShipper = useRef('topShipper');
    this.invoiceBill = useRef('invoiceBill');
    onWillStart(async () => {
      let freightData = await this.orm.call('dashboard.details', 'get_freight_info', []);
      if (freightData) {
        this.state.freightStats = freightData;
      }
    });
    onMounted(() => {
      this.renderFreightDirection();
      this.renderFreightStages();
      // Graph
      this.renderMoveType();
      this.renderShipmentMonth();
      this.renderTopConsignee();
      this.renderTopShipper();
      this.renderInvoiceBill();
    })
  }
  viewDashboardStatic(type) {
    let model = 'freight.shipment';
    let name;
    let domain = [];
    if (type == 'air') {
      name = 'Air Shipment'
      domain = [['transport', '=', 'air']]
    } else if (type == 'ocean') {
      name = 'Ocean Shipment'
      domain = [['transport', '=', 'ocean']]
    } else if (type == 'land') {
      name = 'Land Shipment'
      domain = [['transport', '=', 'land']]
    } else if (type == 'house') {
      name = 'House Shipment'
      domain = [['operation', '=', 'house']]
    } else if (type == 'direct') {
      name = 'Direct Shipment'
      domain = [['operation', '=', 'direct']]
    } else if (type == 'master') {
      name = 'Master Shipment'
      domain = [['operation', '=', 'master']]
    } else if (type == 'pending_booking') {
      name = 'Pending Booking'
      model = 'shipment.freight.booking'
      domain = [['state', '=', 'draft']]
    } else if (type == 'port') {
      name = 'Ports'
      model = 'freight.port'
      domain = []
    } else if (type == 'total_shipment') {
      name = 'Total Shipment'
      domain = []
    } else if (type == 'pending_quat') {
      name = 'Pending Quotation'
      domain = [['status', '=', 'q']]
      model = 'shipment.quotation'
    } else if (type == 'shipper') {
      name = 'Shippers'
      domain = [['shipper', '=', true]]
      model = 'res.partner'
    } else if (type == 'consignee') {
      name = 'Shippers'
      domain = [['consignee', '=', true]]
      model = 'res.partner'
    }
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: name,
      res_model: model,
      view_mode: 'kanban',
      views: [[false, 'list'], [false, 'form']],
      target: 'current',
      context: { 'create': false },
      domain: domain,
    });
  }

  renderFreightDirection() {
    let data = this.state.freightStats['freight_direction']
    const options = {
      series: [{
        name: 'Import',
        data: [data[1][0]]
      }, {
        name: 'Export',
        data: [data[1][1]]
      }],
      chart: {
        type: 'bar',
        height: 420,
        toolbar: {
          show: false,
        },
      },
      colors: ['#FEDD99', '#FFA7B4', '#80BFFF', '#80FFCC'],
      plotOptions: {
        bar: {
          borderRadius: 10,
          horizontal: false,
          columnWidth: '50%',
          endingShape: 'rounded'
        },
      },
      dataLabels: {
        enabled: false
      },
      stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
      },
      xaxis: {
        categories: ['Shipment Direction'],
      },
      yaxis: {
        title: {
          text: 'Count'
        }
      },
      fill: {
        opacity: 1
      },
      legend: {
        show: true,
        fontSize: '11px',
        markers: {
          width: 12,
          height: 12,
          strokeColor: '#fff',
          radius: 12,
        },
      },
      tooltip: {
        y: {
          formatter: function (val) {
            return "" + val + " Shipments"
          }
        }
      }
    };
    this.renderGraph(this.freightDirection.el, options);
  }
  renderFreightStages() {
    let data = this.state.freightStats['shipment_stages']
    const options = {
      series: data[1],
      chart: {
        height: 400,
        type: 'pie',
      },
      colors: ['#F9B16E', '#F9A971', '#F8A174', '#F89977', '#F7907A', '#F7887D', '#F68080'],
      labels: data[0],
      dataLabels: {
        enabled: false,
      },
      legend: {
        position: 'bottom',
        fontSize: '15px',

      },
      dataLabels: {
        enabled: true,
        style: {
          fontSize: '12px',
          colors: ['#57504d'],
          dropShadow: {
            enabled: false,
          }
        },
        dropShadow: {
          enabled: false,
        },
      },
    };
    this.renderGraph(this.freightStages.el, options);
  }
  renderShipmentMonth() {
    const options = {
      series: [{
        name: 'Air',
        data: this.state.freightStats['get_shipment_month'][1],
        color: "#1ED7B5",
      }, {
        name: 'Ocean',
        data: this.state.freightStats['get_shipment_month'][2],
        color: "#87E8AE",
      }, {
        name: 'Land',
        data: this.state.freightStats['get_shipment_month'][3],
        color: "#F0F9A7",
      }],
      chart: {
        type: 'bar',
        height: 350,
        stacked: true,
        toolbar: {
          show: true
        },
        zoom: {
          enabled: true
        }
      },
      dataLabels: {
        enabled: true,
        style: {
          fontSize: '12px',
          colors: ['#57504d'],
          dropShadow: {
            enabled: false,
          }
        },
        dropShadow: {
          enabled: false,
        },
      },
      fill: {
        type: 'gradient',
        gradient: {
          shade: 'dark',
          type: "vertical",
        },
      },
      responsive: [{
        breakpoint: 480,
        options: {
          legend: {
            position: 'bottom',
            offsetX: -10,
            offsetY: 0
          }
        }
      }],
      plotOptions: {
        bar: {
          horizontal: false,
          borderRadius: 10,
          dataLabels: {
            total: {
              enabled: true,
              style: {
                fontSize: '13px',
                fontWeight: 900
              }
            }
          }
        },
      },
      xaxis: {
        categories: this.state.freightStats['get_shipment_month'][0]
      },
      legend: {
        position: 'right',
        offsetY: 40
      },
      fill: {
        opacity: 1
      }
    };
    this.renderGraph(this.shipmentMonth.el, options);
  }
  renderMoveType() {
    const options = {
      series: this.state.freightStats['move_type'][1],
      chart: {
        height: 400,
        type: 'polarArea'
      },
      labels: this.state.freightStats['move_type'][0],
      colors: ['#7DE0AE', '#66C89D', '#4EAF8C', '#37977C', '#207F6B', '#09675B', '#09675B', '#003C3E', '#00272F', '#00121F'],
      fill: {
        opacity: 1
      },
      stroke: {
        width: 1,
        colors: ['#7DE0AE', '#66C89D', '#4EAF8C', '#37977C', '#207F6B', '#09675B', '#09675B', '#003C3E', '#00272F', '#00121F'],
      },
      yaxis: {
        show: false
      },
      fill: {
        type: 'gradient',
        gradient: {
          shade: 'white',
          type: "horizontal",
        },
      },
      legend: {
        position: 'bottom'
      },
      theme: {
        colors: ['#7DE0AE', '#66C89D', '#4EAF8C', '#37977C', '#207F6B', '#09675B', '#09675B', '#003C3E', '#00272F', '#00121F'],
      }
    };
    this.renderGraph(this.moveType.el, options);
  }
  renderTopShipper() {
    const options = {
      series: [{
        name: "Shipments",
        data: this.state.freightStats['top_shipper'][1]
      }],
      chart: {
        height: 350,
        type: 'bar'
      },
      colors: ['#F7B4AE', '#F5A3A0', '#F28F8B', '#F08380', '#ED6F6C'],
      plotOptions: {
        bar: {
          columnWidth: '30%',
          distributed: true,
        }
      },
      dataLabels: {
        enabled: false
      },
      legend: {
        show: false
      },
      xaxis: {
        categories: this.state.freightStats['top_shipper'][0],
        labels: {
          style: {
            colors: '#000C66',
            fontSize: '12px'
          }
        }
      }
    };
    this.renderGraph(this.topShipper.el, options);
  }
  renderTopConsignee() {
    const options = {
      series: [{
        name: "Amount",
        data: this.state.freightStats['top_consign'][1]
      }],
      chart: {
        height: 350,
        type: 'bar',
      },
      colors: ['#f29e4c', '#f1c453', '#efea5a', '#b9e769', '#83e377', '#16db93', '#0db39e', '#048ba8', '#2c699a', '#54478c'],
      plotOptions: {
        bar: {
          columnWidth: '30%',
          distributed: true,
        }
      },
      dataLabels: {
        enabled: false
      },
      legend: {
        show: false
      },
      xaxis: {
        categories: this.state.freightStats['top_consign'][0],
        labels: {
          style: {
            colors: '#000C66',
            fontSize: '12px'
          }
        }
      }
    };
    this.renderGraph(this.topConsignee.el, options);
  }
  renderInvoiceBill() {
    const options = {
      series: [{
        name: 'Bills',
        data: this.state.freightStats['get_bill_invoice'][1],
        color: "#91E5DB",

      }, {
        name: 'Invoice',
        data: this.state.freightStats['get_bill_invoice'][2],
        color: "#AAB2FF",
      }],
      chart: {
        type: 'bar',
        height: 350,
        stacked: true,
        toolbar: {
          show: true
        },
        zoom: {
          enabled: true
        }
      },
      responsive: [{
        breakpoint: 480,
        options: {
          legend: {
            position: 'bottom',
            offsetX: -10,
            offsetY: 0
          }
        }
      }],
      plotOptions: {
        bar: {
          horizontal: false,
          borderRadius: 1,
          dataLabels: {
            total: {
              enabled: true,
              style: {
                fontSize: '13px',
                fontWeight: 900
              }
            }
          }
        },
      },
      xaxis: {
        categories: this.state.freightStats['get_bill_invoice'][0]
      },
      legend: {
        position: 'right',
        offsetY: 40
      },
      fill: {
        opacity: 1
      }
    };

    this.renderGraph(this.invoiceBill.el, options);
  }
  renderGraph(el, options) {
    const graphData = new ApexCharts(el, options);
    graphData.render();
  }
}
FreightDashboard.template = "tk_freight.template_freight_dashboard";
registry.category("actions").add("freight_dashboard", FreightDashboard);