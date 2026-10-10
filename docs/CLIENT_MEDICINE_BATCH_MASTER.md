# Client Medicine & Batch Master

## Functional scope

The Administration workspace now provides a data-driven medicine master and medicine-batch management layer.

### Medicine master

- Search active medicines.
- Create a medicine.
- Update medicine metadata.
- Activate/deactivate an existing medicine.

### Medicine batches

For a selected medicine:

- View active and inactive batches.
- Create a batch.
- Edit batch manufacturer, dates, prices, stock, minimum stock, storage and active state.
- Show expiry and stock information.

The client uses the existing medicine and medicine-batch APIs; no new clinical or pharmacy data model is introduced.

## Workflow relationship

```text
Medicine Master
      ↓
Medicine Batch
      ↓
Available pharmacy stock
      ↓
Prescription dispensing
```

The existing dispensing transaction remains server-authoritative.
