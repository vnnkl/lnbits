window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  data() {
    return {
      selectedWallet: null,
      arrangements: [],
      loading: false,
      columns: [
        {
          name: 'merchant_wallet',
          label: 'Merchant',
          field: 'merchant_wallet',
          align: 'left',
          sortable: true
        },
        {
          name: 'total_debt_sats',
          label: 'Total Debt (sats)',
          field: 'total_debt_sats',
          align: 'right',
          sortable: true
        },
        {
          name: 'repaid_sats',
          label: 'Repaid (sats)',
          field: 'repaid_sats',
          align: 'right',
          sortable: true
        },
        {
          name: 'remaining_debt',
          label: 'Remaining (sats)',
          field: 'remaining_debt',
          align: 'right',
          sortable: true
        },
        {
          name: 'progress_percent',
          label: 'Progress',
          field: 'progress_percent',
          align: 'center',
          sortable: true
        },
        {
          name: 'reroute_percent',
          label: 'Reroute %',
          field: 'reroute_percent',
          align: 'right',
          sortable: true
        },
        {
          name: 'status',
          label: 'Status',
          field: 'status',
          align: 'center',
          sortable: true
        },
        {
          name: 'created_at',
          label: 'Created',
          field: 'created_at',
          align: 'left',
          sortable: true
        }
      ]
    }
  },
  watch: {
    selectedWallet() {
      this.getArrangements()
    }
  },
  methods: {
    getArrangements() {
      if (!this.selectedWallet) return
      this.loading = true
      LNbits.api.request(
          'GET',
          '/orangepiller/api/v1/arrangements',
          this.selectedWallet.adminkey
        )
        .then(response => {
          this.arrangements = response.data.map(a => ({
            ...a,
            remaining_debt: a.total_debt_sats - a.repaid_sats,
            progress_percent: (
              a.total_debt_sats > 0
                ? (a.repaid_sats / a.total_debt_sats * 100).toFixed(2)
                : '100.00'
            )
          }))
        })
        .catch(err => {
          LNbits.utils.notifyApiError(err)
        })
        .finally(() => {
          this.loading = false
        })
    }
  },
  created() {
    this.selectedWallet = this.g.user.wallets[0]
  }
})
