<template>
  <div class="container main-layout">
    <div class="row mb-4">
      <div class="col">
        <header>
          <h2 class="header_logo">ERPNext Workflow</h2>
        </header>
      </div>
    </div>

    <div class="row">
      <!-- Sidebar for Department Color Legend with Clickable Menu -->
      <div class="col-md-3">
        <label class="font-weight-bold">Departments</label>
        <div class="legend">
          <div
            class="d-flex align-items-center mb-2 clickable"
            v-for="dept in departments"
            :key="dept.department"
            @click="selectDepartment(dept.department)"
          >
            <div
              class="mr-2"
              :style="{
                backgroundColor: dept.department_color || 'black',
                width: '15px',
                height: '15px',
              }"
            ></div>
            <span>{{ dept.name }}</span>
          </div>
        </div>
      </div>

      <!-- Process Dropdown and Content -->
      <div class="col-md-9">
        <div class="row mb-3">
          <div class="col-md-6">
            <label class="font-weight-bold">Select Process</label>
            <div class="input-group">
              <select
                class="custom-select"
                v-model="selectedProcess"
                @change="updateWorkflow"
              >
                <option
                  v-for="(item, key) in filteredWorkflows"
                  :key="key"
                  :value="key"
                >
                  {{ item.title }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <div v-for="(item, key) in workflowsToShow" :key="key" class="row mb-3">
          <div class="col">
            <h4>{{ item.title }}</h4>
            <div v-html="item.description"></div>
            <button
              class="btn btn-primary mt-3"
              @click="item.show = !item.show"
            >
              {{ item.show ? "Hide" : "Show" }} Flowchart
            </button>
            <div v-if="item.show" class="mt-3">
              <img
                  :src="item.chartImage"
                  alt="Workflow Chart"
                  class="img-fluid border rounded cursor-pointer"
                  @click="openZoom(item.chartImage)"
                />

            <!-- Zoom Modal -->
            <div v-if="zoomImage" class="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50" @click="zoomImage = null">
              <img :src="zoomImage" class="max-w-full max-h-full border-4 border-white rounded shadow-lg" />
            </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "ProcessFlow",
  data() {
    return {
      workflows: {},
      selectedProcess: "",
      selectedDepartment: "",
      departments: [], // dynamic from backend
      zoomImage: null,
    };
  },
  computed: {
    filteredWorkflows() {
      if (!this.selectedDepartment) return this.workflows;
      return Object.fromEntries(
        Object.entries(this.workflows).filter(
          ([_, wf]) => wf.department === this.selectedDepartment
        )
      );
    },
    workflowsToShow() {
      if (
        this.selectedProcess &&
        this.filteredWorkflows[this.selectedProcess]
      ) {
        return {
          [this.selectedProcess]: this.filteredWorkflows[this.selectedProcess],
        };
      }
      return this.filteredWorkflows;
    },
  },
  methods: {
    updateWorkflow() {
      Object.values(this.workflows).forEach((p) => (p.show = false));
    },
    selectDepartment(dept) {
      this.selectedDepartment = dept;
      const firstProcess = Object.entries(this.workflows).find(
        ([_key, wf]) => wf.department === dept
      );
      if (firstProcess) {
        this.selectedProcess = firstProcess[0];
      }
      this.updateWorkflow();
    },
    fetchDepartments() {
      let me = this;
      frappe.call({
        method:
          "genie.genie.page.process_flow.process_flow.get_departments",
        callback: function (r) {
          me.departments = r.message;
          // me.departments = r.message.map((dep) => ({
          //   department: dep.name,
          //   department_name: dep.department,

          //   department_color: dep.department_color || "#6c757d",
          // }));
        },
      });
    },
    fetchWorkflows() {
      let me = this;
      frappe.call({
        method:
          "genie.genie.page.process_flow.process_flow.get_workflows",
        callback: function (r) {
          const workflows = {};
          r.message.forEach((doc) => {
            workflows[doc.name] = {
              title: doc.title,
              description: doc.description,
              chartImage: doc.chart_image,
              department: doc.department,
              show: false,
            };
          });
          me.workflows = workflows;
          me.selectDepartment("Sales");
        },
      });
    },
    openZoom(imageUrl) {
      this.zoomImage = imageUrl;
    },
  },
  mounted() {
    this.fetchDepartments();
    this.fetchWorkflows();
  },
};
</script>

<style scoped>
.main-layout header {
  width: 100%;
  height: 100px;
  font-weight: bold;
  text-align: center;
  background: #ffd700;
  transition: 0.3s;
}

.header_logo {
  font-family: "Oswald", sans-serif;
  margin: 0;
  padding-top: 40px;
  font-size: 40px;
  text-shadow: 3px 4px rgba(0, 0, 0, 0.1);
}

.img-fluid {
  max-width: 100%;
  height: auto;
  border: 1px solid #ccc;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.legend div {
  margin-bottom: 4px;
}

.clickable {
  cursor: pointer;
}

.clickable:hover {
  text-decoration: underline;
  opacity: 0.8;
}
.zoom-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
</style>
