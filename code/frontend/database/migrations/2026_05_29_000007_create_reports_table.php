<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('reports', function (Blueprint $table) {
            $table->id();

            $table->string('source');
            $table->string('title');
            $table->string('url')->nullable();
            $table->string('teaser')->nullable();
            $table->longText('body')->nullable();
            $table->date('report_date');

            $table->string('admin_level_1')->nullable()->index();
            $table->string('admin_level_2')->nullable();
            $table->string('admin_level_3')->nullable();

            $table->decimal('relevance_score', 5, 2)->nullable();
            $table->string('relevance_score_string')->nullable();
            $table->decimal('distance_km', 8, 2)->nullable();

            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('reports');
    }
};
