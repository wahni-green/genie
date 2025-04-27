import Court from './process.vue';
import { createApp } from 'vue';

frappe.provide('genie');

genie.ProcessFlow = class ProcessFlow {
    constructor({ wrapper, page }) {
        this.$wrapper = wrapper;
        let $container = $('<div>');
        $container.appendTo(this.$wrapper);
        this.page = page;
        $('.page-head').remove();
        let app = createApp(Court);
        let $vm = app.mount($container.get(0))
    }
}