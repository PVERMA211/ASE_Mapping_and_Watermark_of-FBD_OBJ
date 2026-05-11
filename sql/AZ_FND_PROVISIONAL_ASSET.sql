/******************************************************
** Name                 : [AZ_FND_NEST_SF].[AZ_FND_PROVISIONAL_ASSET]
** Description          : This table holds provisional asset details from SF
** Author               : Pradeep
** Created On           : 2026/05/05
**
** Modification History
** ------------ ---------- -----------------------
** [yyyy/mm/dd]    [modifier]     [description_of_changes]
**  2026/05/05      Pradeep        Initial - Added Provisional Asset table
 *******************************************************/

CREATE TABLE [AZ_FND_NEST_SF].[AZ_FND_PROVISIONAL_ASSET]
(
	[CreatedById] [varchar](255) NULL,
	[CreatedDate] [datetime] NULL,
	[Id] [varchar](255) NULL,
	[IsDeleted] [varchar](255) NULL,
	[LastModifiedById] [varchar](255) NULL,
	[LastModifiedDate] [datetime] NULL,
	[Name] [varchar](255) NULL,
	[OwnerId] [varchar](255) NULL,
	[RecordTypeId] [varchar](255) NULL,
	[ST_IsVoid__c] VARCHAR(5) NULL,
	[ST_WorkOrderLineItem__c] VARCHAR(30) NULL,
	[ST_WorkOrder__c] VARCHAR(30) NULL,
	[ST_Asset__c] VARCHAR(30) NULL,
	[ST_IsNewAsset__c] VARCHAR(5) NULL,
	[ST_AssetScriptCompleted__c] VARCHAR(5) NULL,
	[ST_RailwayID__c] VARCHAR(50) NULL,
	[ST_AssetGroup__c] VARCHAR(255) NULL,
	[ST_AssetType__c] VARCHAR(255) NULL,
	[ST_AssetStatus__c] VARCHAR(255) NULL,
	[ST_ConstructionDetails__c] VARCHAR(MAX) NULL,
	[ST_SupportedEquipment__c] VARCHAR(MAX) NULL,
	[ST_SupportedEquipmentComments__c] VARCHAR(255) NULL,
	[ST_SecondaryEquipment__c] VARCHAR(MAX) NULL,
	[ST_SecondaryEquipmentComments__c] VARCHAR(255) NULL,
	[ST_AssetHas__c] VARCHAR(MAX) NULL,
	[ST_PrimaryELR__c] VARCHAR(30) NULL,
	[ST_StartMilage__c] NUMERIC(8,4) NULL,
	[ST_AncillaryPositionRelativetoTrack__c] VARCHAR(255) NULL,
	[ST_PositionRelativetoTrackComments__c] VARCHAR(255) NULL,
	[ST_Side__c] VARCHAR(255) NULL,
	[ST_FoundationLocation__c] VARCHAR(255) NULL,
	[ST_HeightofGradientIfNotLevelGround__c] VARCHAR(255) NULL,
	[ST_BaseArrangement__c] VARCHAR(255) NULL,
	[ST_StructureConstructionForm__c] VARCHAR(255) NULL,
	[ST_DefineandRefertoAEComments__c] VARCHAR(255) NULL,
	[ST_ElementForm__c] VARCHAR(255) NULL,
	[ST_NoofVerticalElements__c] NUMERIC(6) NULL,
	[ST_NoofHorizontalElements__c] NUMERIC(6) NULL,
	[ST_LengthofHorizontalElementm__c] NUMERIC(8,3) NULL,
	[ST_PrimaryMaterial__c] VARCHAR(255) NULL,
	[ST_Coating__c] VARCHAR(255) NULL,
	[ST_HeightEstimatem__c] NUMERIC(5,2) NULL,
	[ST_DimensionAmm__c] NUMERIC(6,2) NULL,
	[ST_DimensionBmm__c] NUMERIC(6,2) NULL,
	[ST_AssetName__c] VARCHAR(255) NULL,
	[ST_Centroid__c] VARCHAR(20) NULL,
	[ST_AssetHierarchyStatus__c] VARCHAR(255) NULL,
	[ST_GeneralComments__c] VARCHAR(MAX) NULL,
	[ST_OwningParty__c] VARCHAR(255) NULL,
	[ST_HCEElementexists__c] VARCHAR(255) NULL,
	[ST_AssetCommissioningStatus__c] VARCHAR(255) NULL,
	[ST_MajorStructure__c] VARCHAR(255) NULL,
	[SystemModstamp] DATETIME NULL,
	[AZ_EFFECTIVE_FROM_DT] DATETIME NULL,
	[AZ_EFFECTIVE_TO_DT] DATETIME NULL,
	[AZ_ACTIVE_ROW_FLAG] VARCHAR(1) NULL
) ON [PRIMARY]
GO
