window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  data() {
    return {
      selectedWallet: null,
      arrangements: [],
      loading: false,
      merchantArrangements: [],
      merchantLoading: false,
      showEditDialog: false,
      editForm: {id: '', reroute_percent: 50},
      showForgiveDialog: false,
      forgiveArrangementId: '',
      showQrDialog: false,
      qrDialogUrl: '',
      showOnboardDialog: false,
      onboardForm: {
        debt_amount: null,
        reroute_percent: 50,
        merchant_name: '',
        currency: 'sat',
        tip_options: '',
        tax_default: 0,
        tax_inclusive: true,
        business_name: '',
        business_address: '',
        business_vat_id: ''
      },
      currencyOptions: ['sat', 'USD', 'EUR', 'GBP', 'CHF', 'JPY', 'CAD', 'AUD', 'BRL', 'MXN'],
      onboardLoading: false,
      columns: [
        {
          name: 'merchant_wallet',
          label: 'Merchant',
          field: 'merchant_wallet',
          align: 'left',
          sortable: true
        },
        {
          name: 'merchant_name',
          label: 'Merchant Name',
          field: 'merchant_name',
          align: 'left',
          sortable: true
        },
        {
          name: 'tpos',
          label: 'TPoS',
          field: 'tpos_url',
          align: 'center',
          sortable: false
        },
        {
          name: 'merchant_credentials',
          label: 'Credentials',
          field: 'merchant_credentials',
          align: 'left',
          sortable: false
        },
        {
          name: 'total_debt_sats',
          label: 'Total Debt',
          field: 'debt_display',
          align: 'right',
          sortable: true
        },
        {
          name: 'repaid_sats',
          label: 'Repaid',
          field: 'repaid_display',
          align: 'right',
          sortable: true
        },
        {
          name: 'remaining_debt',
          label: 'Remaining',
          field: 'remaining_display',
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
        },
        {
          name: 'actions',
          label: 'Actions',
          field: 'actions',
          align: 'center',
          sortable: false
        }
      ],
      merchantColumns: [
        {
          name: 'orange_piller_wallet',
          label: 'Orange Piller',
          field: 'orange_piller_wallet',
          align: 'left',
          sortable: true
        },
        {
          name: 'tpos',
          label: 'TPoS',
          field: 'tpos_url',
          align: 'center',
          sortable: false
        },
        {
          name: 'total_debt_sats',
          label: 'Total Debt',
          field: 'debt_display',
          align: 'right',
          sortable: true
        },
        {
          name: 'repaid_sats',
          label: 'Repaid',
          field: 'repaid_display',
          align: 'right',
          sortable: true
        },
        {
          name: 'remaining_debt',
          label: 'Remaining',
          field: 'remaining_display',
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
        }
      ]
    }
  },
  watch: {
    selectedWallet() {
      this.getArrangements()
      this.getMerchantArrangements()
    }
  },
  methods: {
    showQr(url) {
      this.qrDialogUrl = url
      this.showQrDialog = true
    },
    openOnboardDialog() {
      this.onboardForm = {
        debt_amount: null,
        reroute_percent: 50,
        merchant_name: '',
        currency: 'sat',
        tip_options: '',
        tax_default: 0,
        tax_inclusive: true,
        business_name: '',
        business_address: '',
        business_vat_id: ''
      }
      this.showOnboardDialog = true
    },
    createArrangement() {
      if (!this.onboardForm.debt_amount || this.onboardForm.debt_amount <= 0) {
        this.$q.notify({type: 'warning', message: 'Debt amount must be greater than 0'})
        return
      }
      if (this.onboardForm.reroute_percent < 1 || this.onboardForm.reroute_percent > 100) {
        this.$q.notify({type: 'warning', message: 'Reroute percent must be between 1 and 100'})
        return
      }
      this.onboardLoading = true
      const isSat = this.onboardForm.currency === 'sat'
      const payload = {
        total_debt_sats: isSat ? parseInt(this.onboardForm.debt_amount) : 0,
        total_debt_fiat: isSat ? null : parseFloat(this.onboardForm.debt_amount),
        debt_currency: this.onboardForm.currency,
        reroute_percent: parseInt(this.onboardForm.reroute_percent),
        merchant_name: this.onboardForm.merchant_name || null,
        currency: this.onboardForm.currency || 'sat',
        tip_options: this.onboardForm.tip_options || null,
        tax_default: parseFloat(this.onboardForm.tax_default) || 0,
        tax_inclusive: this.onboardForm.tax_inclusive,
        business_name: this.onboardForm.business_name || null,
        business_address: this.onboardForm.business_address || null,
        business_vat_id: this.onboardForm.business_vat_id || null
      }
      LNbits.api.request(
          'POST',
          '/orangepiller/api/v1/arrangements',
          this.selectedWallet.adminkey,
          payload
        )
        .then(response => {
          this.showOnboardDialog = false
          const arr = response.data
          let msg = 'Merchant onboarded successfully!'
          if (arr.warning) {
            msg += ' ⚠️ ' + arr.warning
          }
          this.$q.notify({type: arr.warning ? 'warning' : 'positive', message: msg, timeout: 8000})
          if (arr.merchant_credentials) {
            LNbits.utils.copyText(arr.merchant_credentials)
            this.$q.notify({type: 'info', message: 'Merchant login URL copied to clipboard', timeout: 4000})
          }
          this.getArrangements()
        })
        .catch(err => {
          LNbits.utils.notifyApiError(err)
        })
        .finally(() => {
          this.onboardLoading = false
        })
    },
    _mapArrangement(a) {
      const isFiat = a.debt_currency && a.debt_currency !== 'sat'
      let remaining, progress, debtDisplay, repaidDisplay, remainingDisplay
      if (isFiat) {
        remaining = (a.total_debt_fiat || 0) - (a.repaid_fiat || 0)
        if (remaining < 0) remaining = 0
        progress = a.total_debt_fiat > 0
          ? ((a.repaid_fiat || 0) / a.total_debt_fiat * 100).toFixed(2)
          : '100.00'
        debtDisplay = a.total_debt_fiat.toFixed(2) + ' ' + a.debt_currency
        repaidDisplay = (a.repaid_fiat || 0).toFixed(2) + ' ' + a.debt_currency
        remainingDisplay = remaining.toFixed(2) + ' ' + a.debt_currency
      } else {
        remaining = a.total_debt_sats - a.repaid_sats
        if (remaining < 0) remaining = 0
        progress = a.total_debt_sats > 0
          ? (a.repaid_sats / a.total_debt_sats * 100).toFixed(2)
          : '100.00'
        debtDisplay = a.total_debt_sats.toLocaleString() + ' sats'
        repaidDisplay = a.repaid_sats.toLocaleString() + ' sats'
        remainingDisplay = remaining.toLocaleString() + ' sats'
      }
      return {
        ...a,
        remaining_debt: remaining,
        progress_percent: progress,
        debt_display: debtDisplay,
        repaid_display: repaidDisplay,
        remaining_display: remainingDisplay
      }
    },
    _detectCompletionTransitions(oldList, newList, labelFn) {
      const oldStatusById = {}
      oldList.forEach(a => { oldStatusById[a.id] = a.status })
      newList.forEach(a => {
        if (a.status === 'completed' && oldStatusById[a.id] && oldStatusById[a.id] !== 'completed') {
          this.$q.notify({
            type: 'positive',
            message: labelFn(a),
            timeout: 5000
          })
        }
      })
    },
    getArrangements() {
      if (!this.selectedWallet) return
      this.loading = true
      LNbits.api.request(
          'GET',
          '/orangepiller/api/v1/arrangements',
          this.selectedWallet.adminkey
        )
        .then(response => {
          const newList = response.data.map(a => this._mapArrangement(a))
          this._detectCompletionTransitions(
            this.arrangements, newList,
            a => 'Arrangement completed! Debt fully repaid for merchant ' + (a.merchant_name || a.merchant_wallet)
          )
          this.arrangements = newList
        })
        .catch(err => {
          LNbits.utils.notifyApiError(err)
        })
        .finally(() => {
          this.loading = false
        })
    },
    getMerchantArrangements() {
      if (!this.selectedWallet) return
      this.merchantLoading = true
      LNbits.api.request(
          'GET',
          '/orangepiller/api/v1/merchant/arrangements',
          this.selectedWallet.adminkey
        )
        .then(response => {
          const newList = response.data.map(a => this._mapArrangement(a))
          this._detectCompletionTransitions(
            this.merchantArrangements, newList,
            a => 'Arrangement completed! Debt fully repaid by ' + a.orange_piller_wallet
          )
          this.merchantArrangements = newList
        })
        .catch(err => {
          // 404 or empty is expected when wallet is not a merchant
          this.merchantArrangements = []
        })
        .finally(() => {
          this.merchantLoading = false
        })
    },
    openEditDialog(arrangement) {
      this.editForm.id = arrangement.id
      this.editForm.reroute_percent = arrangement.reroute_percent
      this.showEditDialog = true
    },
    updateArrangement() {
      if (this.editForm.reroute_percent < 1 || this.editForm.reroute_percent > 100) {
        this.$q.notify({type: 'warning', message: 'Reroute percent must be between 1 and 100'})
        return
      }
      LNbits.api.request(
          'PUT',
          '/orangepiller/api/v1/arrangements/' + this.editForm.id,
          this.selectedWallet.adminkey,
          {reroute_percent: parseInt(this.editForm.reroute_percent)}
        )
        .then(() => {
          this.$q.notify({type: 'positive', message: 'Reroute percent updated'})
          this.showEditDialog = false
          this.getArrangements()
        })
        .catch(err => {
          LNbits.utils.notifyApiError(err)
        })
    },
    openForgiveDialog(arrangement) {
      this.forgiveArrangementId = arrangement.id
      this.showForgiveDialog = true
    },
    forgiveArrangement() {
      LNbits.api.request(
          'PUT',
          '/orangepiller/api/v1/arrangements/' + this.forgiveArrangementId,
          this.selectedWallet.adminkey,
          {forgive: true}
        )
        .then(() => {
          this.$q.notify({type: 'positive', message: 'Debt forgiven — arrangement completed'})
          this.showForgiveDialog = false
          this.getArrangements()
        })
        .catch(err => {
          LNbits.utils.notifyApiError(err)
        })
    }
  },
  created() {
    this.selectedWallet = this.g.user.wallets[0]
  }
})
