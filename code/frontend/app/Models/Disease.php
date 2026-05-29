<?php

namespace App\Models;

use Database\Factories\DiseaseFactory;
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

#[Fillable(['name'])]
class Disease extends Model
{
    /** @use HasFactory<DiseaseFactory> */
    use HasFactory;
}
