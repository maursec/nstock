import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

type Page = 'Dashboard' | 'Products' | 'Stock Movements' | 'Purchase Orders' | 'Suppliers' | 'Team';
type Product = {
  id: number; sku: string; name: string; category: string; supplier: string;
  unitCost: number; unitPrice: number; reorderPoint: number; stock: number; active: boolean;
};
type Movement = { date: string; product: string; type: string; quantity: number; user: string; note: string };
type PurchaseOrder = { id: number; supplier: string; createdBy: string; status: string; orderDate: string; expectedDate: string; lines: number; total: number };
type Supplier = { id: number; name: string; contact: string; email: string; phone: string; products: number };
type TeamMember = { name: string; email: string; role: string; initials: string };

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html'
})
export class AppComponent {
  pages: Page[] = ['Dashboard', 'Products', 'Stock Movements', 'Purchase Orders', 'Suppliers', 'Team'];
  activePage: Page = 'Dashboard';
  search = '';
  productCategory = 'All categories';
  productStatus = 'Active';
  movementFilter = 'All movements';
  poFilter = 'All statuses';
  showAddProduct = false;
  showAddSupplier = false;
  showMovementForm = false;
  showOrderForm = false;
  toast = '';
  selectedProduct: Product | null = null;

  products: Product[] = [
    {id:1,sku:'BEV-001',name:'Sparkling Water 12oz',category:'Beverages',supplier:'Coastal Beverage Co.',unitCost:.40,unitPrice:1.25,reorderPoint:24,stock:16,active:true},
    {id:2,sku:'BEV-002',name:'Cold Brew Coffee 11oz',category:'Beverages',supplier:'Coastal Beverage Co.',unitCost:1.80,unitPrice:4.50,reorderPoint:12,stock:16,active:true},
    {id:3,sku:'BEV-003',name:'Orange Juice 16oz',category:'Beverages',supplier:'Coastal Beverage Co.',unitCost:1.50,unitPrice:3.75,reorderPoint:12,stock:4,active:true},
    {id:4,sku:'BEV-004',name:'Green Tea 16oz',category:'Beverages',supplier:'Coastal Beverage Co.',unitCost:.90,unitPrice:2.50,reorderPoint:18,stock:23,active:true},
    {id:5,sku:'SNK-001',name:'Trail Mix 6oz',category:'Snacks',supplier:'Harbor Snack Supply',unitCost:1.10,unitPrice:3.00,reorderPoint:10,stock:8,active:true},
    {id:6,sku:'SNK-002',name:'Kettle Chips 2oz',category:'Snacks',supplier:'Harbor Snack Supply',unitCost:.55,unitPrice:1.75,reorderPoint:24,stock:29,active:true},
    {id:7,sku:'SNK-003',name:'Protein Bar',category:'Snacks',supplier:'Harbor Snack Supply',unitCost:1.20,unitPrice:2.99,reorderPoint:15,stock:28,active:true},
    {id:8,sku:'SNK-004',name:'Dark Chocolate Bar',category:'Snacks',supplier:'Harbor Snack Supply',unitCost:1.00,unitPrice:2.75,reorderPoint:12,stock:10,active:true},
    {id:9,sku:'HSE-001',name:'Paper Towels 2pk',category:'Household',supplier:'CleanPro Wholesale',unitCost:2.10,unitPrice:4.99,reorderPoint:8,stock:14,active:true},
    {id:10,sku:'HSE-002',name:'Dish Soap 16oz',category:'Household',supplier:'CleanPro Wholesale',unitCost:1.40,unitPrice:3.49,reorderPoint:6,stock:5,active:true},
    {id:11,sku:'HSE-003',name:'Trash Bags 20ct',category:'Household',supplier:'CleanPro Wholesale',unitCost:3.00,unitPrice:6.99,reorderPoint:6,stock:13,active:true},
    {id:12,sku:'PRC-001',name:'Hand Sanitizer 8oz',category:'Personal Care',supplier:'Acme Distributing',unitCost:1.25,unitPrice:3.99,reorderPoint:10,stock:18,active:true},
    {id:13,sku:'PRC-002',name:'Toothpaste 4oz',category:'Personal Care',supplier:'Acme Distributing',unitCost:1.60,unitPrice:3.79,reorderPoint:8,stock:15,active:true},
    {id:14,sku:'PRC-003',name:'Lip Balm',category:'Personal Care',supplier:'Acme Distributing',unitCost:.60,unitPrice:1.99,reorderPoint:12,stock:16,active:true},
    {id:15,sku:'SNK-005',name:'Summer Fruit Gummies',category:'Snacks',supplier:'Harbor Snack Supply',unitCost:.80,unitPrice:2.25,reorderPoint:0,stock:0,active:false},
    {id:16,sku:'HOM-901',name:'Scented Candle (Pumpkin Spice)',category:'Beverages',supplier:'Acme Distributing',unitCost:4.50,unitPrice:12.99,reorderPoint:4,stock:23,active:true}
  ];

  suppliers: Supplier[] = [
    {id:1,name:'Acme Distributing',contact:'Pat Lee',email:'pat@acme.test',phone:'562-555-0101',products:3},
    {id:2,name:'Coastal Beverage Co.',contact:'Sam Ortiz',email:'sam@coastal.test',phone:'562-555-0102',products:4},
    {id:3,name:'Harbor Snack Supply',contact:'Jordan Wu',email:'jordan@harbor.test',phone:'562-555-0103',products:5},
    {id:4,name:'CleanPro Wholesale',contact:'Riley Brooks',email:'riley@cleanpro.test',phone:'562-555-0104',products:3}
  ];

  team: TeamMember[] = [
    {name:'Maria Lopez',email:'maria@nstock.test',role:'Owner',initials:'ML'},
    {name:'Devon Price',email:'devon@nstock.test',role:'Staff',initials:'DP'},
    {name:'Aisha Khan',email:'aisha@nstock.test',role:'Staff',initials:'AK'}
  ];

  orders: PurchaseOrder[] = [
    {id:1,supplier:'Coastal Beverage Co.',createdBy:'Maria Lopez',status:'Received',orderDate:'Sep 01, 2026',expectedDate:'Sep 03, 2026',lines:4,total:187.20},
    {id:2,supplier:'Harbor Snack Supply',createdBy:'Maria Lopez',status:'Received',orderDate:'Sep 02, 2026',expectedDate:'Sep 04, 2026',lines:5,total:172.80},
    {id:3,supplier:'CleanPro Wholesale',createdBy:'Maria Lopez',status:'Received',orderDate:'Sep 05, 2026',expectedDate:'Sep 08, 2026',lines:3,total:127.80},
    {id:4,supplier:'Acme Distributing',createdBy:'Devon Price',status:'Received',orderDate:'Sep 08, 2026',expectedDate:'Sep 10, 2026',lines:3,total:96.15},
    {id:5,supplier:'Coastal Beverage Co.',createdBy:'Maria Lopez',status:'Ordered',orderDate:'Oct 08, 2026',expectedDate:'Oct 14, 2026',lines:2,total:62.40},
    {id:6,supplier:'Harbor Snack Supply',createdBy:'Devon Price',status:'Draft',orderDate:'—',expectedDate:'—',lines:2,total:50.40}
  ];

  movements: Movement[] = [
    {date:'Oct 07, 2026 · 5:00 PM',product:'Lip Balm',type:'Sale',quantity:-20,user:'Devon Price',note:'Register sale'},
    {date:'Oct 06, 2026 · 5:00 PM',product:'Toothpaste 4oz',type:'Sale',quantity:-9,user:'Aisha Khan',note:'Register sale'},
    {date:'Oct 06, 2026 · 11:45 AM',product:'Hand Sanitizer 8oz',type:'Sale',quantity:-12,user:'Devon Price',note:'Register sale'},
    {date:'Oct 05, 2026 · 8:30 AM',product:'Orange Juice 16oz',type:'Adjustment',quantity:-2,user:'Maria Lopez',note:'Expired, discarded'},
    {date:'Oct 05, 2026 · 5:00 PM',product:'Trash Bags 20ct',type:'Sale',quantity:-5,user:'Aisha Khan',note:'Register sale'},
    {date:'Oct 04, 2026 · 5:00 PM',product:'Dish Soap 16oz',type:'Sale',quantity:-13,user:'Devon Price',note:'Register sale'},
    {date:'Oct 03, 2026 · 5:00 PM',product:'Dark Chocolate Bar',type:'Sale',quantity:-26,user:'Devon Price',note:'Register sale'},
    {date:'Oct 02, 2026 · 8:30 AM',product:'Kettle Chips 2oz',type:'Adjustment',quantity:-3,user:'Maria Lopez',note:'Damaged bags found in stock'},
    {date:'Oct 01, 2026 · 12:10 PM',product:'Protein Bar',type:'Return',quantity:1,user:'Aisha Khan',note:'Customer return, unopened'},
    {date:'Oct 01, 2026 · 5:00 PM',product:'Sparkling Water 12oz',type:'Sale',quantity:-35,user:'Devon Price',note:'Register sale'},
    {date:'Sep 10, 2026 · 11:45 AM',product:'Hand Sanitizer 8oz',type:'Receive',quantity:30,user:'Maria Lopez',note:'Purchase order #4'},
    {date:'41 days ago',product:'Scented Candle (Pumpkin Spice)',type:'Sale',quantity:-1,user:'Demo workspace',note:'Seed refresh: seasonal item'},
    {date:'60 days ago',product:'Scented Candle (Pumpkin Spice)',type:'Receive',quantity:24,user:'Demo workspace',note:'Seasonal order'}
  ];

  newProduct = {name:'',sku:'',category:'Beverages',supplier:'Coastal Beverage Co.',unitCost:0,unitPrice:0,reorderPoint:0,stock:0};
  newSupplier = {name:'',contact:'',email:'',phone:''};
  newMovement = {productId:1,type:'Sale',quantity:1,note:''};
  newOrder = {supplier:'Coastal Beverage Co.',productId:1,quantity:1};

  get saleMovementCount(): number { return this.movements.filter(m => m.type === 'Sale').length; }
  get receiveMovementCount(): number { return this.movements.filter(m => m.type === 'Receive').length; }
  get orderedOrderCount(): number { return this.orders.filter(o => o.status === 'Ordered').length; }
  get draftOrderCount(): number { return this.orders.filter(o => o.status === 'Draft').length; }

  readonly demoToday = new Date();
  get slowMoverSpotlight(): Product | undefined { return this.products.find(p => p.sku === 'HOM-901'); }
  get activeProducts(): Product[] { return this.products.filter(p => p.active); }
  get lowStock(): Product[] { return this.activeProducts.filter(p => p.stock <= p.reorderPoint); }
  get totalUnits(): number { return this.activeProducts.reduce((n,p) => n + p.stock, 0); }
  get retailValue(): number { return this.activeProducts.reduce((n,p) => n + p.stock * p.unitPrice, 0); }
  get costValue(): number { return this.activeProducts.reduce((n,p) => n + p.stock * p.unitCost, 0); }
  get filteredProducts(): Product[] {
    const term = this.search.toLowerCase();
    return this.products.filter(p =>
      (this.productStatus === 'All' || (this.productStatus === 'Active' ? p.active : !p.active)) &&
      (this.productCategory === 'All categories' || p.category === this.productCategory) &&
      `${p.name} ${p.sku} ${p.supplier}`.toLowerCase().includes(term)
    );
  }
  get filteredMovements(): Movement[] {
    return this.movements.filter(m => this.movementFilter === 'All movements' || m.type === this.movementFilter);
  }
  get filteredOrders(): PurchaseOrder[] {
    return this.orders.filter(o => this.poFilter === 'All statuses' || o.status === this.poFilter);
  }
  get categoryCounts(): {name:string;count:number}[] {
    return ['Beverages','Snacks','Household','Personal Care'].map(name => ({name,count:this.activeProducts.filter(p=>p.category===name).length}));
  }
  get selectedOrderProduct(): Product {
    return this.products.find(p=>p.id===Number(this.newOrder.productId)) ?? this.products[0];
  }
  setPage(page: Page): void { this.activePage = page; this.search = ''; }
  isLow(p: Product): boolean { return p.active && p.stock <= p.reorderPoint; }
  notify(message: string): void {
    this.toast = message;
    setTimeout(() => this.toast = '', 2600);
  }
  addProduct(): void {
    if (!this.newProduct.name.trim() || !this.newProduct.sku.trim()) return;
    const id = Math.max(...this.products.map(p=>p.id)) + 1;
    this.products.unshift({...this.newProduct,id,stock:Number(this.newProduct.stock),unitCost:Number(this.newProduct.unitCost),unitPrice:Number(this.newProduct.unitPrice),reorderPoint:Number(this.newProduct.reorderPoint),active:true});
    this.showAddProduct = false;
    this.newProduct = {name:'',sku:'',category:'Beverages',supplier:'Coastal Beverage Co.',unitCost:0,unitPrice:0,reorderPoint:0,stock:0};
    this.notify('Product added to the demo inventory.');
  }
  addSupplier(): void {
    if (!this.newSupplier.name.trim()) return;
    this.suppliers.push({...this.newSupplier,id:Math.max(...this.suppliers.map(s=>s.id))+1,products:0});
    this.showAddSupplier = false;
    this.newSupplier = {name:'',contact:'',email:'',phone:''};
    this.notify('Supplier added to the demo workspace.');
  }
  recordMovement(): void {
    const product = this.products.find(p=>p.id===Number(this.newMovement.productId));
    const qty = Math.max(1,Number(this.newMovement.quantity));
    if (!product) return;
    let signed = qty;
    if (this.newMovement.type === 'Sale' || this.newMovement.type === 'Adjustment out') signed = -qty;
    if (product.stock + signed < 0) { this.notify('Not enough stock available for this movement.'); return; }
    product.stock += signed;
    this.movements.unshift({date:new Date().toLocaleString('en-US', {dateStyle:'medium', timeStyle:'short'}),product:product.name,type:this.newMovement.type === 'Adjustment out' ? 'Adjustment' : this.newMovement.type,quantity:signed,user:'Maria Lopez',note:this.newMovement.note || 'Added in demo'});
    this.showMovementForm = false;
    this.notify('Stock movement recorded.');
  }
  createOrder(): void {
    const p = this.selectedOrderProduct;
    this.orders.unshift({id:Math.max(...this.orders.map(o=>o.id))+1,supplier:this.newOrder.supplier,createdBy:'Maria Lopez',status:'Draft',orderDate:'—',expectedDate:'—',lines:1,total:Number(this.newOrder.quantity)*p.unitCost});
    this.showOrderForm = false;
    this.notify('Draft purchase order created.');
  }
  receiveOrder(order: PurchaseOrder): void {
    if (order.status !== 'Ordered') return;
    order.status = 'Received';
    this.notify(`Purchase order #${order.id} marked received in the UI demo.`);
  }
  openProduct(p: Product): void { this.selectedProduct = p; }
  saveProduct(): void { this.selectedProduct = null; this.notify('Product details updated in the UI demo.'); }
}
