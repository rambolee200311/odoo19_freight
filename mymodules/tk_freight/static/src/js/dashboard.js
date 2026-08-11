import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { getDefaultConfig } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { useDebounced } from "@web/core/utils/timing";
import { session } from "@web/session";
import { Domain } from "@web/core/domain";
import { sprintf } from "@web/core/utils/strings";

const { Component, useSubEnv, useState, onMounted, onWillStart, onWillUnmount, useRef } = owl;
import { loadJS, loadCSS } from "@web/core/assets"

// ========== 全局工具函数 ==========
const getSafeLang = () => {
    if (!session || !session.user_context || !session.user_context.lang) return 'en_US';
    const lang = session.user_context.lang.toLowerCase().replace(/[-_]/g, '_');
    return lang.includes('zh') ? 'zh_CN' : 'en_US';
};

const safeGet = (obj, path, defaultValue = []) => {
    return path.reduce((acc, curr) => (acc && acc[curr] !== undefined) ? acc[curr] : defaultValue, obj);
};

const getDashboardTemplateId = () => {
    const lang = getSafeLang();
    return lang === 'zh_CN' 
        ? "tk_freight.template_freight_dashboard_cn" 
        : "tk_freight.template_freight_dashboard";
};

// ========== 主组件 ==========
class FreightDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");

        // 核心修复：声明所有图表Ref
        this.freightDirection = useRef('freightDirection');
        this.freightStages = useRef('freightStages');
        this.shipmentMonth = useRef('shipmentMonth');
        this.moveType = useRef('moveType');
        this.topShipper = useRef('topShipper');
        this.topConsignee = useRef('topConsignee');
        this.invoiceBill = useRef('invoiceBill');

        this.state = useState({
            freightStats: {
                freight_direction: [[], [0, 0]],
                shipment_stages: [[], []],
                get_shipment_month: [[], [], [], []],
                move_type: [[], []],
                top_shipper: [[], []],
                top_consign: [[], []],
                get_bill_invoice: [[], [], []],
                total_shipment: 0,
                pending_quat: 0,
                pending_booking: 0,
                total_port: 0,
                shipper_count: 0,
                consignee_count: 0,
                house_count: 0,
                direct_count: 0,
                master_count: 0,
                air: 0,
                ocean: 0,
                land: 0
            },
            langText: {},
            currentLang: getSafeLang()
        });

        useSubEnv({
            config: {
                ...getDefaultConfig(),
                ...this.env.config,
            },
        });

        // 初始化多语言映射
        this.initLangText();
        this.loadLanguageCSS();

        // 全局错误捕获方法
        this.catchChartError = (fn, chartName) => {
            try {
                fn();
            } catch (error) {
                console.error(`渲染${chartName}图表失败:`, error);
            }
        };

        onWillStart(async () => {
            try {
                const freightData = await this.orm.call('dashboard.details', 'get_freight_info', []);
                if (freightData && typeof freightData === 'object') {
                    this.state.freightStats = { ...this.state.freightStats, ...freightData };
                }
            } catch (error) {
                console.error('加载货运数据失败:', error);
                // 数据加载失败时提供默认值
                this.state.freightStats = {
                    ...this.state.freightStats,
                    freight_direction: [['进口', '出口'], [0, 0]],
                    shipment_stages: [['待处理', '已完成'], [0, 0]]
                };
            }
        });
        
        onMounted(() => {
            // 延迟渲染图表（延长至300ms确保DOM挂载）
            setTimeout(() => {
                this.catchChartError(() => this.renderFreightDirection(), '货运方向');
                this.catchChartError(() => this.renderFreightStages(), '订单状态');
                this.catchChartError(() => this.renderMoveType(), '运输类型');
                this.catchChartError(() => this.renderShipmentMonth(), '月度货运量');
                this.catchChartError(() => this.renderTopConsignee(), 'TOP5收货方');
                this.catchChartError(() => this.renderTopShipper(), 'TOP5发货方');
                this.catchChartError(() => this.renderInvoiceBill(), '月度发票账单');
            }, 300);
            // 监听语言变化
            window.addEventListener('language-change', this.observeLangChange);
        });

        onWillUnmount(() => {
            window.removeEventListener('language-change', this.observeLangChange);
            // 销毁所有图表实例
            [this.freightDirection, this.freightStages, this.shipmentMonth, this.moveType, 
             this.topShipper, this.topConsignee, this.invoiceBill].forEach(ref => {
                if (ref.el && ref.el._apexChart) {
                    ref.el._apexChart.destroy();
                }
                if (ref.el && ref.el._echartInstance) {
                    ref.el._echartInstance.dispose();
                }
            });
        });
    }

    // 多语言文本映射
    initLangText() {
        this.langTextMap = {
            'en_US': {
                'Shipments': 'Shipments',
                'Pending Quotations': 'Pending Quotations',
                'Pending Bookings': 'Pending Bookings',
                'Ports': 'Ports',
                'Shipper': 'Shipper',
                'Consignee': 'Consignee',
                'Shipment Statics': 'Shipment Statics',
                'House': 'House',
                'Direct': 'Direct',
                'Master': 'Master',
                'Air': 'Air',
                'Ocean': 'Ocean',
                'Land': 'Land',
                'Direction': 'Direction',
                'Status': 'Status',
                'Shipment by Month': 'Shipment by Month',
                'Move Type': 'Move Type',
                'Top 5 Shipper': 'Top 5 Shipper',
                'Top 5 Consignee': 'Top 5 Consignee',
                'Invoices and Bills by Month': 'Invoices and Bills by Month',
                'Shipment Direction': 'Shipment Direction',
                'Count': 'Count',
                'Import': 'Import',
                'Export': 'Export',
                'Amount': 'Amount',
                'Bills': 'Bills',
                'Invoice': 'Invoice',
                'Air Shipment': 'Air Shipment',
                'Ocean Shipment': 'Ocean Shipment',
                'Land Shipment': 'Land Shipment',
                'House Shipment': 'House Shipment',
                'Direct Shipment': 'Direct Shipment',
                'Master Shipment': 'Master Shipment',
                'Pending Booking': 'Pending Booking',
                'Total Shipment': 'Total Shipment',
                'Pending Quotation': 'Pending Quotation',
                'Shippers': 'Shippers',
                'Consignees': 'Consignees',
                'No Data': 'No Data',
                'Orders': 'Orders'
            },
            'zh_CN': {
                'Shipments': '货运订单',
                'Pending Quotations': '待处理报价',
                'Pending Bookings': '待处理订舱',
                'Ports': '港口数量',
                'Shipper': '发货方',
                'Consignee': '收货方',
                'Shipment Statics': '货运统计',
                'House': '分单',
                'Direct': '直单',
                'Master': '主单',
                'Air': '空运',
                'Ocean': '海运',
                'Land': '陆运',
                'Direction': '运输方向',
                'Status': '订单状态',
                'Shipment by Month': '月度货运量',
                'Move Type': '运输类型',
                'Top 5 Shipper': 'TOP5发货方',
                'Top 5 Consignee': 'TOP5收货方',
                'Invoices and Bills by Month': '月度发票与账单',
                'Shipment Direction': '运输方向',
                'Count': '数量',
                'Import': '进口',
                'Export': '出口',
                'Amount': '金额',
                'Bills': '账单',
                'Invoice': '发票',
                'Air Shipment': '空运订单',
                'Ocean Shipment': '海运订单',
                'Land Shipment': '陆运订单',
                'House Shipment': '分单订单',
                'Direct Shipment': '直单订单',
                'Master Shipment': '主单订单',
                'Pending Booking': '待处理订舱',
                'Total Shipment': '全部订单',
                'Pending Quotation': '待处理报价',
                'Shippers': '发货方',
                'Consignees': '收货方',
                'No Data': '暂无数据',
                'Orders': '订单数'
            }
        };
    }

    // 切换语言文本
    switchLangText() {
        const lang = getSafeLang();
        this.state.currentLang = lang;
        this.state.langText = this.langTextMap[lang] || this.langTextMap['en_US'];
        this.render();
    }

    // 加载语言对应的CSS
    async loadLanguageCSS() {
        const lang = getSafeLang();
        const cssFileName = lang === 'zh_CN' ? 'dashboard_CN' : 'dashboard';
        const cssPath = `/tk_freight/static/src/css/${cssFileName}.css`;
        
        try {
            await loadCSS(cssPath);
        } catch (error) {
            console.error(`加载CSS失败: ${cssPath}`, error);
        } finally {
            this.switchLangText();
        }
    }

    // 监听语言变化
    observeLangChange = () => {
        const newLang = getSafeLang();
        if (newLang !== this.state.currentLang) {
            this.state.currentLang = newLang;
            this.switchLangText();
            this.loadLanguageCSS();
            this.renderAllCharts();
        }
    };

    // 重新渲染所有图表
    renderAllCharts() {
        this.catchChartError(() => this.renderFreightDirection(), '货运方向');
        this.catchChartError(() => this.renderFreightStages(), '订单状态');
        this.catchChartError(() => this.renderMoveType(), '运输类型');
        this.catchChartError(() => this.renderShipmentMonth(), '月度货运量');
        this.catchChartError(() => this.renderTopConsignee(), 'TOP5收货方');
        this.catchChartError(() => this.renderTopShipper(), 'TOP5发货方');
        this.catchChartError(() => this.renderInvoiceBill(), '月度发票账单');
    }

    // 货运方向图表渲染
    renderFreightDirection() {
        const langText = this.state.langText;
        const directionRef = this.freightDirection;
        
        // 容错：Ref或el不存在
        if (!directionRef || !directionRef.el) {
            console.warn('货运方向图表容器未找到');
            return;
        }
        const container = directionRef.el;

        // 容错数据
        const directionData = safeGet(this.state, ['freightStats', 'freight_direction'], [[], [0, 0]]);
        const importCount = Array.isArray(directionData[1]) ? (directionData[1][0] || 0) : 0;
        const exportCount = Array.isArray(directionData[1]) ? (directionData[1][1] || 0) : 0;

        const option = {
            title: { text: langText['Shipment Direction'], left: 'center' },
            tooltip: { trigger: 'axis' },
            legend: { data: [langText['Import'], langText['Export']], bottom: 0 },
            xAxis: {
                type: 'category',
                data: [langText['Direction']],
                axisLabel: { fontSize: 12 }
            },
            yAxis: {
                type: 'value',
                name: langText['Count'],
                axisLabel: { formatter: '{value}' }
            },
            series: [
                {
                    name: langText['Import'],
                    type: 'bar',
                    data: [importCount]
                },
                {
                    name: langText['Export'],
                    type: 'bar',
                    data: [exportCount]
                }
            ]
        };

        // 初始化ECharts
        if (window.echarts) {
            // 销毁旧实例
            if (container._echartInstance) {
                container._echartInstance.dispose();
            }
            const chart = window.echarts.init(container);
            chart.setOption(option);
            window.addEventListener('resize', () => chart.resize());
            container._echartInstance = chart;
        } else {
            console.error('ECharts库未加载');
        }
    }

    // 订单状态图表渲染
    renderFreightStages() {
        if (!this.freightStages || !this.freightStages.el) {
            console.warn('货运阶段图表容器未找到');
            return;
        }

        const shipmentStages = safeGet(this.state, ['freightStats', 'shipment_stages'], [[], []]);
        const labels = Array.isArray(shipmentStages[0]) ? shipmentStages[0] : [this.state.langText['No Data']];
        const series = Array.isArray(shipmentStages[1]) ? shipmentStages[1] : [0];

        if (labels.length === 0 || series.length === 0) {
            labels.push(this.state.langText['No Data']);
            series.push(100);
        }

        const options = {
            series: series,
            chart: { height: 400, type: 'pie' },
            colors: ['#F9B16E', '#F9A971', '#F8A174', '#F89977', '#F7907A', '#F7887D', '#F68080'],
            labels: labels,
            dataLabels: {
                enabled: true,
                style: { fontSize: '12px', colors: ['#57504d'], dropShadow: { enabled: false } },
                dropShadow: { enabled: false }
            },
            legend: { position: 'bottom', fontSize: '15px' }
        };
        
        this.renderGraph(this.freightStages.el, options);
    }

    // 月度货运订单图表
    renderShipmentMonth() {
        if (!this.shipmentMonth || !this.shipmentMonth.el) {
            console.warn('月度货运订单图表容器未找到');
            return;
        }

        const langText = this.state.langText;
        const monthData = safeGet(this.state, ['freightStats', 'get_shipment_month'], [[], [], [], []]);
        const categories = Array.isArray(monthData[0]) ? monthData[0] : ['1月', '2月', '3月', '4月', '5月', '6月'];
        const airData = Array.isArray(monthData[1]) ? monthData[1] : [0, 0, 0, 0, 0, 0];
        const oceanData = Array.isArray(monthData[2]) ? monthData[2] : [0, 0, 0, 0, 0, 0];
        const landData = Array.isArray(monthData[3]) ? monthData[3] : [0, 0, 0, 0, 0, 0];

        const options = {
            series: [{
                name: langText['Air'] || '空运',
                data: airData,
                color: "#1ED7B5"
            }, {
                name: langText['Ocean'] || '海运',
                data: oceanData,
                color: "#87E8AE"
            }, {
                name: langText['Land'] || '陆运',
                data: landData,
                color: "#F0F9A7"
            }],
            chart: {
                type: 'bar',
                height: 350,
                stacked: true,
                toolbar: { show: true },
                zoom: { enabled: true }
            },
            dataLabels: {
                enabled: true,
                style: { fontSize: '12px', colors: ['#57504d'], dropShadow: { enabled: false } },
                dropShadow: { enabled: false }
            },
            fill: {
                type: 'gradient',
                gradient: { shade: 'dark', type: "vertical" }
            },
            responsive: [{
                breakpoint: 480,
                options: { legend: { position: 'bottom', offsetX: -10, offsetY: 0 } }
            }],
            plotOptions: {
                bar: {
                    horizontal: false,
                    borderRadius: 10,
                    dataLabels: {
                        total: { enabled: true, style: { fontSize: '13px', fontWeight: 900 } }
                    }
                }
            },
            xaxis: { 
                categories: categories,
                labels: { show: true }
            },
            legend: { position: 'right', offsetY: 40 },
            fill: { opacity: 1 }
        };
        this.renderGraph(this.shipmentMonth.el, options);
    }

    // 运输类型图表
    renderMoveType() {
        if (!this.moveType || !this.moveType.el) {
            console.warn('运输类型图表容器未找到');
            return;
        }

        const moveData = safeGet(this.state, ['freightStats', 'move_type'], [[], []]);
        const labels = Array.isArray(moveData[0]) ? moveData[0] : [this.state.langText['Air'], this.state.langText['Ocean'], this.state.langText['Land']];
        const series = Array.isArray(moveData[1]) ? moveData[1] : [0, 0, 0];

        const options = {
            series: series,
            chart: { height: 400, type: 'polarArea' },
            labels: labels,
            colors: ['#7DE0AE', '#66C89D', '#4EAF8C', '#37977C', '#207F6B', '#09675B', '#09675B', '#003C3E', '#00272F', '#00121F'],
            fill: { opacity: 1 },
            stroke: {
                width: 1,
                colors: ['#7DE0AE', '#66C89D', '#4EAF8C', '#37977C', '#207F6B', '#09675B', '#09675B', '#003C3E', '#00272F', '#00121F']
            },
            yaxis: { show: false },
            fill: {
                type: 'gradient',
                gradient: { shade: 'white', type: "horizontal" }
            },
            legend: { position: 'bottom' },
            theme: { colors: ['#7DE0AE', '#66C89D', '#4EAF8C', '#37977C', '#207F6B', '#09675B', '#09675B', '#003C3E', '#00272F', '#00121F'] }
        };
        this.renderGraph(this.moveType.el, options);
    }

    // TOP5发货方图表
    renderTopShipper() {
        if (!this.topShipper || !this.topShipper.el) {
            console.warn('TOP5发货方图表容器未找到');
            return;
        }

        const langText = this.state.langText;
        const shipperData = safeGet(this.state, ['freightStats', 'top_shipper'], [[], []]);
        const categories = Array.isArray(shipperData[0]) ? shipperData[0] : ['发货方1', '发货方2', '发货方3', '发货方4', '发货方5'];
        const series = Array.isArray(shipperData[1]) ? shipperData[1] : [0, 0, 0, 0, 0];

        const options = {
            series: [{
                name: langText['Orders'] || '订单数',
                data: series
            }],
            chart: { height: 350, type: 'bar' },
            colors: ['#F7B4AE', '#F5A3A0', '#F28F8B', '#F08380', '#ED6F6C'],
            plotOptions: { bar: { columnWidth: '30%', distributed: true } },
            dataLabels: { enabled: false },
            legend: { show: false },
            xaxis: {
                categories: categories,
                labels: { 
                    style: { colors: '#000C66', fontSize: '12px' },
                    show: true
                }
            }
        };
        this.renderGraph(this.topShipper.el, options);
    }

    // TOP5收货方图表
    renderTopConsignee() {
        if (!this.topConsignee || !this.topConsignee.el) {
            console.warn('TOP5收货方图表容器未找到');
            return;
        }

        const langText = this.state.langText;
        const consignData = safeGet(this.state, ['freightStats', 'top_consign'], [[], []]);
        const categories = Array.isArray(consignData[0]) ? consignData[0] : ['收货方1', '收货方2', '收货方3', '收货方4', '收货方5'];
        const series = Array.isArray(consignData[1]) ? consignData[1] : [0, 0, 0, 0, 0];

        const options = {
            series: [{
                name: langText['Amount'] || '金额',
                data: series
            }],
            chart: { height: 350, type: 'bar' },
            colors: ['#f29e4c', '#f1c453', '#efea5a', '#b9e769', '#83e377', '#16db93', '#0db39e', '#048ba8', '#2c699a', '#54478c'],
            plotOptions: { bar: { columnWidth: '30%', distributed: true } },
            dataLabels: { enabled: false },
            legend: { show: false },
            xaxis: {
                categories: categories,
                labels: { 
                    style: { colors: '#000C66', fontSize: '12px' },
                    show: true
                }
            }
        };
        this.renderGraph(this.topConsignee.el, options);
    }

    // 月度发票账单图表
    renderInvoiceBill() {
        if (!this.invoiceBill || !this.invoiceBill.el) {
            console.warn('月度发票账单图表容器未找到');
            return;
        }

        const langText = this.state.langText;
        const invoiceData = safeGet(this.state, ['freightStats', 'get_bill_invoice'], [[], [], []]);
        const categories = Array.isArray(invoiceData[0]) ? invoiceData[0] : ['1月', '2月', '3月', '4月', '5月', '6月'];
        const billsData = Array.isArray(invoiceData[1]) ? invoiceData[1] : [0, 0, 0, 0, 0, 0];
        const invoiceDataArr = Array.isArray(invoiceData[2]) ? invoiceData[2] : [0, 0, 0, 0, 0, 0];

        const options = {
            series: [{
                name: langText['Bills'] || '账单',
                data: billsData,
                color: "#91E5DB"
            }, {
                name: langText['Invoice'] || '发票',
                data: invoiceDataArr,
                color: "#AAB2FF"
            }],
            chart: {
                type: 'bar',
                height: 350,
                stacked: true,
                toolbar: { show: true },
                zoom: { enabled: true }
            },
            responsive: [{
                breakpoint: 480,
                options: { legend: { position: 'bottom', offsetX: -10, offsetY: 0 } }
            }],
            plotOptions: {
                bar: {
                    horizontal: false,
                    borderRadius: 1,
                    dataLabels: {
                        total: { enabled: true, style: { fontSize: '13px', fontWeight: 900 } }
                    }
                }
            },
            xaxis: { 
                categories: categories,
                labels: { show: true }
            },
            legend: { position: 'right', offsetY: 40 },
            fill: { opacity: 1 }
        };
        this.renderGraph(this.invoiceBill.el, options);
    }

    // 通用图表渲染方法（带容错和销毁旧实例）
    renderGraph(el, options) {
        if (!el || !window.ApexCharts) {
            console.warn('图表容器不存在或ApexCharts未加载');
            return;
        }

        // 兜底无数据
        if (!options.series || options.series.length === 0) {
            options.series = [{ 
                name: this.state.langText['No Data'] || '暂无数据', 
                data: [0] 
            }];
        }
        if (options.xaxis && !options.xaxis.categories) {
            options.xaxis.categories = [this.state.langText['No Data'] || '暂无数据'];
        }

        try {
            // 销毁旧图表
            if (el._apexChart) {
                el._apexChart.destroy();
            }
            const chart = new ApexCharts(el, options);
            chart.render();
            el._apexChart = chart;
        } catch (error) {
            console.error('渲染图表失败:', error);
        }
    }

    // 预留：点击卡片跳转统计详情
    viewDashboardStatic(type) {
        // 可根据业务需求实现跳转逻辑
        console.log('查看统计详情:', type);
    }
}

// 绑定模板ID
FreightDashboard.template = getDashboardTemplateId();

// 注册组件
registry.category("actions").add("freight_dashboard", FreightDashboard);